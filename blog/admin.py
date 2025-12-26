"""
Blog App Admin Configuration

Rich admin interface for managing blog content.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import (
    BlogCategory,
    BlogTag,
    NewsSource,
    BlogPost,
    BlogPostReference,
    BlogImage,
    BlogComment,
    BlogSubscription
)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    """Admin interface for blog categories."""
    list_display = ['name', 'slug', 'parent', 'get_post_count', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'order')
        }),
        ('Media', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_post_count(self, obj):
        count = obj.posts.filter(status='published', is_deleted=False).count()
        return count
    get_post_count.short_description = 'Posts'


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    """Admin interface for blog tags."""
    list_display = ['name', 'slug', 'get_post_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def get_post_count(self, obj):
        return obj.posts.filter(status='published', is_deleted=False).count()
    get_post_count.short_description = 'Posts'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    """Admin interface for news sources."""
    list_display = [
        'name', 'slug', 'get_logo_preview', 'website_url',
        'is_verified', 'credibility_score', 'get_post_count',
        'is_active', 'order', 'created_at'
    ]
    list_filter = ['is_verified', 'is_active', 'credibility_score', 'created_at']
    search_fields = ['name', 'description', 'website_url']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'get_logo_preview_large']
    ordering = ['order', 'name']
    list_editable = ['order', 'is_active', 'is_verified']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Branding', {
            'fields': ('logo', 'get_logo_preview_large', 'website_url')
        }),
        ('Credibility', {
            'fields': ('is_verified', 'credibility_score'),
            'description': 'Set verification status and credibility score (1-10)'
        }),
        ('Display', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width:40px; max-height:40px; object-fit:contain;" />',
                obj.logo.url
            )
        return '-'
    get_logo_preview.short_description = 'Logo'

    def get_logo_preview_large(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width:200px; max-height:100px; object-fit:contain;" />',
                obj.logo.url
            )
        return '-'
    get_logo_preview_large.short_description = 'Logo Preview'

    def get_post_count(self, obj):
        return obj.posts.filter(status='published', is_deleted=False).count()
    get_post_count.short_description = 'Posts'


class BlogPostReferenceInline(admin.TabularInline):
    """
    Inline admin for managing blog post references.
    Allows adding up to 10 references per post directly in the post admin.
    """
    model = BlogPostReference
    extra = 1  # Show one empty form by default
    max_num = BlogPostReference.MAX_REFERENCES_PER_POST
    min_num = 0
    fields = ['title', 'url', 'author', 'publication_date', 'description', 'order']
    readonly_fields = []
    ordering = ['order', 'created_at']
    verbose_name = 'Reference'
    verbose_name_plural = 'References (Optional - Max 10)'

    classes = ['collapse']  # Collapsible by default

    def get_extra(self, request, obj=None, **kwargs):
        """Show 1 extra form for new posts, 0 for existing posts with references."""
        if obj and obj.references.exists():
            return 0
        return 1


class BlogCommentInline(admin.TabularInline):
    """Inline admin for post comments."""
    model = BlogComment
    extra = 0
    readonly_fields = ['author_name', 'content', 'status', 'created_at']
    fields = ['author_name', 'content', 'status', 'created_at']
    can_delete = True
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


class PostStatusFilter(admin.SimpleListFilter):
    """Custom filter for post status."""
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('draft', 'Draft'),
            ('review', 'Under Review'),
            ('published', 'Published'),
            ('archived', 'Archived'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for blog posts."""
    list_display = [
        'title', 'get_author', 'category', 'get_source_badge',
        'get_status_badge', 'is_featured', 'is_pinned', 'view_count',
        'like_count', 'get_comment_count', 'get_reference_count', 'published_at', 'created_at'
    ]
    list_filter = [
        PostStatusFilter, 'is_featured', 'is_pinned', 'content_type',
        'category', 'source', 'author', 'created_at', 'published_at'
    ]
    search_fields = ['title', 'content', 'excerpt', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'post_id', 'view_count', 'like_count', 'share_count',
        'reading_time_minutes', 'created_at', 'updated_at',
        'deleted_at'
    ]
    filter_horizontal = ['tags', 'related_posts']
    date_hierarchy = 'created_at'
    inlines = [BlogPostReferenceInline, BlogCommentInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'subtitle', 'excerpt', 'content', 'content_type')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt', 'thumbnail', 'video_url')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('News Source', {
            'fields': ('source', 'source_url'),
            'description': 'Select a news source to make the content look authentic (e.g., BBC, CNN)'
        }),
        ('Author & Status', {
            'fields': ('author', 'status', 'published_at')
        }),
        ('Display Options', {
            'fields': ('is_featured', 'is_pinned', 'allow_comments')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Related Posts', {
            'fields': ('related_posts',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'like_count', 'share_count', 'reading_time_minutes'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('post_id', 'is_deleted', 'deleted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']

    def get_author(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return '-'
    get_author.short_description = 'Author'
    get_author.admin_order_field = 'author__username'

    def get_source_badge(self, obj):
        if obj.source:
            verified_icon = '✓ ' if obj.source.is_verified else ''
            return format_html(
                '<span style="background-color:#3498db; color:white; padding:3px 8px; '
                'border-radius:3px; font-size:11px;">{}{}</span>',
                verified_icon, obj.source.name
            )
        return '-'
    get_source_badge.short_description = 'Source'
    get_source_badge.admin_order_field = 'source__name'

    def get_status_badge(self, obj):
        colors = {
            'draft': '#95a5a6',
            'review': '#f39c12',
            'published': '#27ae60',
            'archived': '#7f8c8d',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'

    def get_comment_count(self, obj):
        count = obj.comments.filter(status='approved').count()
        pending = obj.comments.filter(status='pending').count()
        if pending:
            return format_html('{} <span style="color:orange;">(+{})</span>', count, pending)
        return count
    get_comment_count.short_description = 'Comments'

    def get_reference_count(self, obj):
        """Display the number of references for a post."""
        count = obj.references.count()
        if count > 0:
            return format_html(
                '<span style="background-color:#9b59b6; color:white; padding:2px 6px; '
                'border-radius:3px; font-size:11px;">{}</span>',
                count
            )
        return '-'
    get_reference_count.short_description = 'Refs'

    @admin.action(description='Publish selected posts')
    def publish_posts(self, request, queryset):
        updated = queryset.filter(status__in=['draft', 'review']).update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} post(s) published.')

    @admin.action(description='Unpublish selected posts')
    def unpublish_posts(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished.')

    @admin.action(description='Mark as featured')
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} post(s) featured.')

    @admin.action(description='Remove from featured')
    def unfeature_posts(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} post(s) unfeatured.')

    def save_model(self, request, obj, form, change):
        # Set author on creation
        if not change and not obj.author:
            obj.author = request.user

        # Auto-set published_at when publishing
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()

        super().save_model(request, obj, form, change)


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    """Admin interface for blog images."""
    list_display = ['get_thumbnail', 'title', 'alt_text', 'uploaded_by', 'get_dimensions', 'get_file_size', 'created_at']
    list_filter = ['uploaded_by', 'created_at']
    search_fields = ['title', 'alt_text', 'caption']
    readonly_fields = ['image_id', 'file_size', 'width', 'height', 'created_at', 'get_preview']

    fieldsets = (
        ('Image', {
            'fields': ('image', 'get_preview')
        }),
        ('Metadata', {
            'fields': ('title', 'alt_text', 'caption')
        }),
        ('Info', {
            'fields': ('image_id', 'uploaded_by', 'file_size', 'width', 'height', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:80px; max-height:60px; object-fit:cover;" />',
                obj.image.url
            )
        return '-'
    get_thumbnail.short_description = 'Preview'

    def get_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:400px; max-height:300px;" />',
                obj.image.url
            )
        return '-'
    get_preview.short_description = 'Preview'

    def get_dimensions(self, obj):
        if obj.width and obj.height:
            return f'{obj.width}x{obj.height}'
        return '-'
    get_dimensions.short_description = 'Dimensions'

    def get_file_size(self, obj):
        if obj.file_size:
            if obj.file_size > 1024 * 1024:
                return f'{obj.file_size / 1024 / 1024:.1f} MB'
            return f'{obj.file_size / 1024:.1f} KB'
        return '-'
    get_file_size.short_description = 'Size'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


class CommentStatusFilter(admin.SimpleListFilter):
    """Custom filter for comment status."""
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('spam', 'Spam'),
            ('rejected', 'Rejected'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    """Admin interface for blog comments."""
    list_display = [
        'get_comment_preview', 'get_author', 'post', 'get_status_badge',
        'is_highlighted', 'like_count', 'created_at'
    ]
    list_filter = [CommentStatusFilter, 'is_highlighted', 'created_at']
    search_fields = ['content', 'guest_name', 'guest_email', 'user__username', 'post__title']
    readonly_fields = ['comment_id', 'ip_address', 'user_agent', 'created_at', 'updated_at']
    raw_id_fields = ['post', 'parent', 'user']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Comment', {
            'fields': ('post', 'parent', 'content')
        }),
        ('Author', {
            'fields': ('user', 'guest_name', 'guest_email')
        }),
        ('Moderation', {
            'fields': ('status', 'is_highlighted')
        }),
        ('Engagement', {
            'fields': ('like_count',)
        }),
        ('Technical', {
            'fields': ('comment_id', 'ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_comments', 'reject_comments', 'mark_spam']

    def get_comment_preview(self, obj):
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview
    get_comment_preview.short_description = 'Comment'

    def get_author(self, obj):
        return obj.author_name
    get_author.short_description = 'Author'

    def get_status_badge(self, obj):
        colors = {
            'pending': '#f39c12',
            'approved': '#27ae60',
            'spam': '#e74c3c',
            'rejected': '#95a5a6',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} comment(s) approved.')

    @admin.action(description='Reject selected comments')
    def reject_comments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} comment(s) rejected.')

    @admin.action(description='Mark as spam')
    def mark_spam(self, request, queryset):
        updated = queryset.update(status='spam')
        self.message_user(request, f'{updated} comment(s) marked as spam.')


@admin.register(BlogPostReference)
class BlogPostReferenceAdmin(admin.ModelAdmin):
    """
    Admin interface for blog post references.
    Provides a standalone view for managing all references across posts.
    """
    list_display = [
        'title', 'get_post_title', 'get_url_display', 'author',
        'publication_date', 'order', 'created_at'
    ]
    list_filter = ['post__category', 'publication_date', 'created_at']
    search_fields = ['title', 'url', 'author', 'description', 'post__title']
    readonly_fields = ['reference_id', 'created_at', 'updated_at']
    raw_id_fields = ['post']
    ordering = ['post', 'order', 'created_at']
    list_per_page = 25

    fieldsets = (
        ('Post Association', {
            'fields': ('post',)
        }),
        ('Reference Details', {
            'fields': ('title', 'url', 'author', 'description')
        }),
        ('Dates', {
            'fields': ('publication_date', 'accessed_date'),
            'classes': ('collapse',)
        }),
        ('Display', {
            'fields': ('order',)
        }),
        ('System', {
            'fields': ('reference_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_post_title(self, obj):
        """Display truncated post title with link."""
        title = obj.post.title[:40]
        if len(obj.post.title) > 40:
            title += '...'
        return format_html(
            '<a href="/admin/blog/blogpost/{}/change/">{}</a>',
            obj.post.id, title
        )
    get_post_title.short_description = 'Post'
    get_post_title.admin_order_field = 'post__title'

    def get_url_display(self, obj):
        """Display URL as clickable link with truncation."""
        display_url = obj.url[:50]
        if len(obj.url) > 50:
            display_url += '...'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer" '
            'style="color:#3498db;">{}</a>',
            obj.url, display_url
        )
    get_url_display.short_description = 'URL'

    def get_queryset(self, request):
        """Optimize queries by selecting related post."""
        return super().get_queryset(request).select_related('post')


@admin.register(BlogSubscription)
class BlogSubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for blog subscriptions."""
    list_display = ['email', 'name', 'is_verified', 'is_active', 'subscribed_at', 'unsubscribed_at']
    list_filter = ['is_verified', 'is_active', 'subscribed_at']
    search_fields = ['email', 'name']
    readonly_fields = ['verification_token', 'subscribed_at', 'unsubscribed_at']
    filter_horizontal = ['categories']

    fieldsets = (
        ('Subscriber Info', {
            'fields': ('email', 'name')
        }),
        ('Preferences', {
            'fields': ('categories',)
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'verification_token')
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'unsubscribed_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_subscriptions', 'deactivate_subscriptions']

    @admin.action(description='Activate selected subscriptions')
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{updated} subscription(s) activated.')

    @admin.action(description='Deactivate selected subscriptions')
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscription(s) deactivated.')
