"""
Jobs/Careers App Models

This module contains models for job posting functionality.
Supports job listings with categories, filtering, and HTML content.
"""
import uuid
import re
import bleach
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import EmailValidator


class Job(models.Model):
    """
    Job posting model for careers page.
    Supports full-time, part-time, contract, and internship positions.
    """

    # Job type choices
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    # Primary key - UUID for better security and uniqueness
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic information
    title = models.CharField(
        max_length=200,
        help_text="Job title"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL-friendly identifier (auto-generated from title if not provided)"
    )

    # Job details
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Department name (e.g., Engineering, Marketing)"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Job location (e.g., Remote, New York, London)"
    )
    type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Job type"
    )

    # HTML content fields
    description = models.TextField(
        help_text="Job description (HTML content)"
    )
    requirements = models.TextField(
        blank=True,
        null=True,
        help_text="Job requirements (HTML content)"
    )
    responsibilities = models.TextField(
        blank=True,
        null=True,
        help_text="Job responsibilities (HTML content)"
    )

    # Application details
    application_email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Email address for job applications"
    )
    application_method = models.TextField(
        blank=True,
        null=True,
        help_text="Custom application instructions (HTML content)"
    )

    # Status flags
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the job is active/visible"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether the job is featured"
    )

    # Dates
    posted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the job was posted"
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the job expires"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-is_featured', '-posted_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['department']),
            models.Index(fields=['location']),
            models.Index(fields=['type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug and sanitize HTML content."""
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = self._generate_unique_slug()

        # Set posted_at if not set and job is active
        if self.is_active and not self.posted_at:
            self.posted_at = timezone.now()

        # Sanitize HTML content
        self.description = self._sanitize_html(self.description)
        if self.requirements:
            self.requirements = self._sanitize_html(self.requirements)
        if self.responsibilities:
            self.responsibilities = self._sanitize_html(self.responsibilities)
        if self.application_method:
            self.application_method = self._sanitize_html(self.application_method)

        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        """Generate a unique slug from the title."""
        base_slug = slugify(self.title)
        if not base_slug:
            base_slug = 'job'

        slug = base_slug
        counter = 1

        # Check for uniqueness, excluding current instance
        while Job.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @staticmethod
    def _sanitize_html(content):
        """
        Sanitize HTML content to prevent XSS attacks.
        Allows safe HTML tags and attributes.
        """
        if not content:
            return content

        # Allowed HTML tags
        allowed_tags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'a', 'span', 'div',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'blockquote', 'pre', 'code',
            'hr', 'img',
        ]

        # Allowed attributes
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
        }

        # Clean the HTML
        try:
            cleaned = bleach.clean(
                content,
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
            return cleaned
        except Exception:
            # Fallback: strip all HTML tags if bleach fails
            return re.sub(r'<[^>]+>', '', content)

    @property
    def is_expired(self):
        """Check if the job posting has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_visible(self):
        """Check if the job should be visible to public users."""
        return self.is_active and not self.is_expired
