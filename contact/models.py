"""
Contact App Models

This module contains models for contact form submissions.
Users can submit contact forms which are stored for admin review.
"""
import uuid
from django.db import models


class ContactSubmission(models.Model):
    """
    Contact form submission model.
    Stores all contact form submissions from the website.
    """
    CONTACT_TYPE_CHOICES = [
        ('student', 'Student'),
        ('university', 'University'),
        ('agent', 'Agent'),
        ('other', 'Other'),
    ]

    # Unique identifier
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Contact Information
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)

    # Message
    message = models.TextField()

    # Type of inquiry
    type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        default='other'
    )

    # Admin management
    read = models.BooleanField(
        default=False,
        help_text="Whether the submission has been read by admin"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes from admin"
    )

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_submissions'
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.get_type_display()}"
