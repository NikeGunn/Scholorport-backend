"""
Partners App Models

This module contains models for university and agent partners.
Partners are displayed on the homepage and managed by admins.
"""
import uuid
from django.db import models


class Partner(models.Model):
    """
    Partner model for universities and agents.
    Displayed on the homepage partner section.
    """
    PARTNER_TYPE_CHOICES = [
        ('university', 'University'),
        ('agent', 'Agent'),
    ]

    # Unique identifier
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default='university'
    )
    country = models.CharField(max_length=100, blank=True)

    # Visual
    logo = models.ImageField(
        upload_to='partners/logos/',
        blank=True,
        null=True,
        help_text="Partner logo image"
    )

    # Details
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    # Status
    featured = models.BooleanField(
        default=False,
        help_text="Show in featured section on homepage"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether partner is visible on the website"
    )

    # Ordering
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower = first)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partners'
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'
        ordering = ['order', '-featured', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
