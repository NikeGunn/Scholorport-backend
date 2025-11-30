"""
Blog App Models

This module contains models for educational blog/content functionality.
Supports articles, categories, tags, comments, and media uploads.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class BlogCategory(models.Model):
    """
    Categories for organizing blog posts.
    Examples: Study Abroad Tips, University Guides, Visa Information, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    # Visual
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon class name or emoji for category"
    )
    cover_image = models.ImageField(
        upload_to='blog/categories/',
        blank=True,
        null=True
    )

    # Hierarchy (for nested categories)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Ordering
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_categories'
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def post_count(self):
        return self.posts.filter(status='published').count()


class BlogTag(models.Model):
    """
    Tags for blog posts. More granular than categories.
    Examples: IELTS, TOEFL, Scholarship, UK, USA, etc.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_tags'
        verbose_name = 'Blog Tag'
        verbose_name_plural = 'Blog Tags'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """
    Main blog post/article model with full CRUD support.
    Supports rich content, images, SEO, and engagement tracking.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    CONTENT_TYPE_CHOICES = [
        ('article', 'Article'),
        ('guide', 'Guide'),
        ('news', 'News'),
        ('tips', 'Tips & Tricks'),
        ('interview', 'Interview'),
        ('case_study', 'Case Study'),
        ('video', 'Video Content'),
    ]

    # Unique identifier
    post_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # Basic Information
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    excerpt = models.TextField(
        blank=True,
        help_text="Short summary for listings (auto-generated if empty)"
    )

    # Content
    content = models.TextField(help_text="Main article content (supports Markdown/HTML)")
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='article'
    )

    # Media
    featured_image = models.ImageField(
        upload_to='blog/posts/featured/',
        blank=True,
        null=True,
        help_text="Main image for the post (recommended: 1200x630px)"
    )
    featured_image_alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for featured image"
    )
    thumbnail = models.ImageField(
        upload_to='blog/posts/thumbnails/',
        blank=True,
        null=True,
        help_text="Smaller image for listings"
    )

    # Video support
    video_url = models.URLField(
        blank=True,
        help_text="YouTube or Vimeo URL for video content"
    )

    # Categorization
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    tags = models.ManyToManyField(
        BlogTag,
        blank=True,
        related_name='posts'
    )

    # Author
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts'
    )

    # Status and Publishing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # Visibility
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured/hero section"
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin to top of listings"
    )
    allow_comments = models.BooleanField(default=True)

    # Engagement Metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)

    # Reading Time
    reading_time_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Estimated reading time (auto-calculated on save)"
    )

    # SEO
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="SEO title (defaults to title)"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (defaults to excerpt)"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords"
    )
    canonical_url = models.URLField(
        blank=True,
        help_text="Canonical URL if content exists elsewhere"
    )

    # Related Content
    related_posts = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Manually selected related posts"
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['post_id']),
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-generate excerpt
        if not self.excerpt and self.content:
            self.excerpt = self.content[:300].strip() + '...'

        # Calculate reading time (avg 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time_minutes = max(1, round(word_count / 200))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        from django.utils import timezone
        return (
            self.status == 'published' and
            self.published_at and
            self.published_at <= timezone.now()
        )

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class BlogImage(models.Model):
    """
    Media library for blog images.
    Allows reuse across posts and better organization.
    """
    image_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # Image file
    image = models.ImageField(upload_to='blog/media/')

    # Metadata
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)

    # Organization
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_images'
    )

    # File info (auto-populated)
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_images'
        verbose_name = 'Blog Image'
        verbose_name_plural = 'Blog Images'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Only auto-populate if using file upload (not Cloudinary direct upload)
        if self.image and hasattr(self.image, 'size') and not self.file_size:
            try:
                self.file_size = self.image.size
            except:
                self.file_size = 0
            # Get dimensions if possible
            try:
                from PIL import Image
                img = Image.open(self.image)
                self.width, self.height = img.size
            except:
                pass
        # Ensure defaults for required fields
        if not self.file_size:
            self.file_size = 0
        if not self.width:
            self.width = 0
        if not self.height:
            self.height = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Image {self.image_id}"


class BlogComment(models.Model):
    """
    Comments on blog posts.
    Supports nested replies and moderation.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('spam', 'Spam'),
        ('rejected', 'Rejected'),
    ]

    comment_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # Relationships
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Author (can be guest or registered user)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_comments'
    )
    # Guest info (if not logged in)
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)

    # Content
    content = models.TextField()

    # Moderation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_highlighted = models.BooleanField(
        default=False,
        help_text="Highlight as notable comment"
    )

    # Engagement
    like_count = models.PositiveIntegerField(default=0)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_comments'
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
        ]

    def __str__(self):
        author = self.user.username if self.user else self.guest_name
        return f"Comment by {author} on {self.post.title[:30]}"

    @property
    def author_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name

    @property
    def is_reply(self):
        return self.parent is not None


class BlogSubscription(models.Model):
    """
    Email subscriptions for blog updates/newsletter.
    """
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)

    # Preferences
    categories = models.ManyToManyField(
        BlogCategory,
        blank=True,
        help_text="Subscribe to specific categories"
    )

    # Verification
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4)

    # Status
    is_active = models.BooleanField(default=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_subscriptions'
        verbose_name = 'Blog Subscription'
        verbose_name_plural = 'Blog Subscriptions'
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email
