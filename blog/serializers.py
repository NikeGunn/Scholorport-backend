"""
Blog App Serializers

Serializers for blog/educational content API endpoints.
"""
from typing import Optional, List, Dict, Any
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import (
    BlogCategory,
    BlogTag,
    NewsSource,
    BlogPost,
    BlogImage,
    BlogComment,
    BlogSubscription
)


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for author display."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    @extend_schema_field(OpenApiTypes.STR)
    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username


# ============================================================
# CATEGORY SERIALIZERS
# ============================================================

class BlogCategoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing categories."""
    posts_count = serializers.IntegerField(read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'cover_image_url', 'posts_count', 'order', 'is_active'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_cover_image_url(self, obj) -> Optional[str]:
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class BlogCategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed category view."""
    post_count = serializers.IntegerField(read_only=True)
    parent_category = serializers.SerializerMethodField()
    children = BlogCategoryListSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'cover_image', 'cover_image_url', 'parent', 'parent_category',
            'children', 'meta_title', 'meta_description',
            'order', 'is_active', 'post_count', 'created_at', 'updated_at'
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_parent_category(self, obj) -> Optional[Dict[str, Any]]:
        if obj.parent:
            return {'id': obj.parent.id, 'name': obj.parent.name, 'slug': obj.parent.slug}
        return None

    @extend_schema_field(OpenApiTypes.URI)
    def get_cover_image_url(self, obj) -> Optional[str]:
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class BlogCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories."""

    class Meta:
        model = BlogCategory
        fields = [
            'name', 'slug', 'description', 'icon', 'cover_image',
            'parent', 'meta_title', 'meta_description', 'order', 'is_active'
        ]
        extra_kwargs = {
            'slug': {'required': False}
        }

    def validate(self, data):
        """Custom validation to prevent slug conflicts."""
        # If updating, get the instance
        instance = self.instance

        # Check slug uniqueness if provided
        slug = data.get('slug')
        if slug:
            qs = BlogCategory.objects.filter(slug=slug)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'slug': f'Category with slug "{slug}" already exists. Please choose a different slug.'
                })

        # Check name uniqueness
        name = data.get('name')
        if name:
            qs = BlogCategory.objects.filter(name=name)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'name': f'Category with name "{name}" already exists. Please choose a different name.'
                })

        return data


# ============================================================
# TAG SERIALIZERS
# ============================================================

class BlogTagSerializer(serializers.ModelSerializer):
    """Serializer for blog tags."""
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug', 'post_count', 'created_at']
        extra_kwargs = {
            'slug': {'required': False}
        }

    @extend_schema_field(OpenApiTypes.INT)
    def get_post_count(self, obj) -> int:
        return obj.posts.filter(status='published', is_deleted=False).count()


# ============================================================
# NEWS SOURCE SERIALIZERS
# ============================================================

class NewsSourceListSerializer(serializers.ModelSerializer):
    """Serializer for listing news sources."""
    logo_url = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = NewsSource
        fields = [
            'id', 'name', 'slug', 'logo', 'logo_url', 'website_url',
            'description', 'is_verified', 'credibility_score',
            'is_active', 'post_count', 'order'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_logo_url(self, obj) -> Optional[str]:
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_post_count(self, obj) -> int:
        return obj.posts.filter(status='published', is_deleted=False).count()


class NewsSourceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed news source view."""
    logo_url = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = NewsSource
        fields = [
            'id', 'name', 'slug', 'logo', 'logo_url', 'website_url',
            'description', 'is_verified', 'credibility_score',
            'is_active', 'order', 'post_count', 'created_at', 'updated_at'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_logo_url(self, obj) -> Optional[str]:
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_post_count(self, obj) -> int:
        return obj.posts.filter(status='published', is_deleted=False).count()


class NewsSourceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating news sources."""

    class Meta:
        model = NewsSource
        fields = [
            'name', 'slug', 'logo', 'website_url', 'description',
            'is_verified', 'credibility_score', 'is_active', 'order'
        ]
        extra_kwargs = {
            'slug': {'required': False}
        }

    def validate(self, data):
        """Custom validation to prevent conflicts."""
        instance = self.instance

        # Check slug uniqueness if provided
        slug = data.get('slug')
        if slug:
            qs = NewsSource.objects.filter(slug=slug)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'slug': f'News source with slug "{slug}" already exists.'
                })

        # Check name uniqueness
        name = data.get('name')
        if name:
            qs = NewsSource.objects.filter(name=name)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'name': f'News source with name "{name}" already exists.'
                })

        return data


# ============================================================
# IMAGE SERIALIZERS
# ============================================================

class BlogImageSerializer(serializers.ModelSerializer):
    """Serializer for blog images (media library)."""
    image_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = BlogImage
        fields = [
            'id', 'image_id', 'image', 'image_url', 'title', 'alt_text',
            'caption', 'uploaded_by', 'uploaded_by_name',
            'file_size', 'width', 'height', 'created_at'
        ]
        read_only_fields = ['image_id', 'file_size', 'width', 'height', 'created_at']

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj) -> Optional[str]:
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class BlogImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading images."""

    class Meta:
        model = BlogImage
        fields = ['image', 'title', 'alt_text', 'caption']


# ============================================================
# COMMENT SERIALIZERS
# ============================================================

class BlogCommentReplySerializer(serializers.ModelSerializer):
    """Serializer for nested comment replies (no further nesting to avoid recursion)."""
    author_name = serializers.CharField(read_only=True)
    is_reply = serializers.BooleanField(read_only=True)

    class Meta:
        model = BlogComment
        fields = [
            'id', 'comment_id', 'post', 'parent', 'user',
            'guest_name', 'guest_email', 'author_name',
            'content', 'status', 'is_highlighted', 'like_count',
            'is_reply', 'created_at', 'updated_at'
        ]
        read_only_fields = ['comment_id', 'status', 'like_count', 'created_at', 'updated_at']


class BlogCommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments with one level of replies."""
    author_name = serializers.CharField(read_only=True)
    replies = serializers.SerializerMethodField()
    is_reply = serializers.BooleanField(read_only=True)

    class Meta:
        model = BlogComment
        fields = [
            'id', 'comment_id', 'post', 'parent', 'user',
            'guest_name', 'guest_email', 'author_name',
            'content', 'status', 'is_highlighted', 'like_count',
            'is_reply', 'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['comment_id', 'status', 'like_count', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_replies(self, obj) -> List[Dict[str, Any]]:
        """Return one level of replies using non-recursive serializer."""
        if obj.replies.exists():
            return BlogCommentReplySerializer(
                obj.replies.filter(status='approved'),
                many=True,
                context=self.context
            ).data
        return []


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""

    class Meta:
        model = BlogComment
        fields = ['post', 'parent', 'guest_name', 'guest_email', 'content']

    def validate(self, data):
        # Either user or guest info is required
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            data['user'] = request.user
        elif not data.get('guest_name') or not data.get('guest_email'):
            raise serializers.ValidationError({
                'guest_name': 'Name is required for guest comments',
                'guest_email': 'Email is required for guest comments'
            })
        return data


# ============================================================
# POST SERIALIZERS
# ============================================================

class BlogPostListSerializer(serializers.ModelSerializer):
    """Serializer for listing blog posts."""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    source = NewsSourceListSerializer(read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_published = serializers.BooleanField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'post_id', 'title', 'slug', 'subtitle', 'excerpt',
            'content_type', 'featured_image_url', 'thumbnail_url',
            'category', 'category_name', 'category_slug', 'tags',
            'source', 'source_name', 'source_url',
            'author', 'author_name', 'status', 'published_at',
            'is_featured', 'is_pinned', 'is_published',
            'view_count', 'like_count', 'reading_time_minutes',
            'comment_count', 'created_at'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_featured_image_url(self, obj) -> Optional[str]:
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None

    @extend_schema_field(OpenApiTypes.URI)
    def get_thumbnail_url(self, obj) -> Optional[str]:
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_comment_count(self, obj) -> int:
        return obj.comments.filter(status='approved').count()


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed blog post view."""
    author = UserBasicSerializer(read_only=True)
    category = BlogCategoryListSerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    source = NewsSourceDetailSerializer(read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    related_posts = BlogPostListSerializer(many=True, read_only=True)
    is_published = serializers.BooleanField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'post_id', 'title', 'slug', 'subtitle', 'excerpt',
            'content', 'content_type', 'featured_image', 'featured_image_url',
            'featured_image_alt', 'thumbnail', 'thumbnail_url', 'video_url',
            'category', 'tags', 'source', 'source_url',
            'author', 'status', 'published_at',
            'is_featured', 'is_pinned', 'allow_comments', 'is_published',
            'view_count', 'like_count', 'share_count', 'reading_time_minutes',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
            'related_posts', 'comments', 'comment_count',
            'created_at', 'updated_at'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_featured_image_url(self, obj) -> Optional[str]:
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
            return obj.featured_image.url
        return None

    @extend_schema_field(OpenApiTypes.URI)
    def get_thumbnail_url(self, obj) -> Optional[str]:
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_comments(self, obj) -> List[Dict[str, Any]]:
        # Only return top-level approved comments
        comments = obj.comments.filter(status='approved', parent__isnull=True)
        return BlogCommentSerializer(comments, many=True, context=self.context).data

    @extend_schema_field(OpenApiTypes.INT)
    def get_comment_count(self, obj) -> int:
        return obj.comments.filter(status='approved').count()


class BlogPostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating blog posts."""
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
        help_text="List of tag names (will create if not exist)"
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="List of existing tag IDs"
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'subtitle', 'excerpt', 'content', 'content_type',
            'featured_image', 'featured_image_alt', 'thumbnail', 'video_url',
            'category', 'tags', 'tag_ids', 'source', 'source_url',
            'status', 'published_at',
            'is_featured', 'is_pinned', 'allow_comments',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url'
        ]
        extra_kwargs = {
            'slug': {'required': False},
            'excerpt': {'required': False},
            'content': {'required': True, 'error_messages': {'required': 'Content is required for blog post'}},
            'title': {'required': True, 'error_messages': {'required': 'Title is required for blog post'}}
        }

    def validate(self, data):
        """Custom validation for blog posts."""
        # Validate category exists if provided
        if data.get('category') and not BlogCategory.objects.filter(pk=data['category'].pk, is_active=True).exists():
            raise serializers.ValidationError({
                'category': 'Selected category does not exist or is inactive.'
            })

        # Validate source exists if provided
        if data.get('source') and not NewsSource.objects.filter(pk=data['source'].pk, is_active=True).exists():
            raise serializers.ValidationError({
                'source': 'Selected news source does not exist or is inactive.'
            })

        # If source_url is provided, ensure source is also provided
        if data.get('source_url') and not data.get('source'):
            raise serializers.ValidationError({
                'source_url': 'Please select a news source when providing a source URL.'
            })

        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        tag_ids = validated_data.pop('tag_ids', [])

        # Set author from request
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user

        # Auto-publish if status is published and no date set
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()

        post = BlogPost.objects.create(**validated_data)

        # Handle tag names (create if not exist)
        for tag_name in tags_data:
            tag, _ = BlogTag.objects.get_or_create(name=tag_name.strip())
            post.tags.add(tag)

        # Handle tag IDs
        if tag_ids:
            existing_tags = BlogTag.objects.filter(id__in=tag_ids)
            post.tags.add(*existing_tags)

        return post


class BlogPostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating blog posts."""
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'subtitle', 'excerpt', 'content', 'content_type',
            'featured_image', 'featured_image_alt', 'thumbnail', 'video_url',
            'category', 'tags', 'tag_ids', 'source', 'source_url',
            'status', 'published_at',
            'is_featured', 'is_pinned', 'allow_comments',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url'
        ]

    def validate(self, data):
        """Custom validation for blog post updates."""
        # Validate category exists if provided
        if data.get('category') and not BlogCategory.objects.filter(pk=data['category'].pk, is_active=True).exists():
            raise serializers.ValidationError({
                'category': 'Selected category does not exist or is inactive.'
            })

        # Validate source exists if provided
        if data.get('source') and not NewsSource.objects.filter(pk=data['source'].pk, is_active=True).exists():
            raise serializers.ValidationError({
                'source': 'Selected news source does not exist or is inactive.'
            })

        # If source_url is provided, ensure source is also provided
        if data.get('source_url') and not data.get('source'):
            # Check if instance already has a source
            if not self.instance or not self.instance.source:
                raise serializers.ValidationError({
                    'source_url': 'Please select a news source when providing a source URL.'
                })

        return data

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        tag_ids = validated_data.pop('tag_ids', None)

        # Auto-publish if status changed to published
        if validated_data.get('status') == 'published' and not instance.published_at:
            validated_data['published_at'] = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_data is not None:
            instance.tags.clear()
            for tag_name in tags_data:
                tag, _ = BlogTag.objects.get_or_create(name=tag_name.strip())
                instance.tags.add(tag)

        if tag_ids is not None:
            if tags_data is None:
                instance.tags.clear()
            existing_tags = BlogTag.objects.filter(id__in=tag_ids)
            instance.tags.add(*existing_tags)

        return instance


# ============================================================
# SUBSCRIPTION SERIALIZERS
# ============================================================

class BlogSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for blog subscriptions."""
    categories = BlogCategoryListSerializer(many=True, read_only=True)

    class Meta:
        model = BlogSubscription
        fields = [
            'id', 'email', 'name', 'categories', 'is_verified',
            'is_active', 'subscribed_at'
        ]
        read_only_fields = ['is_verified', 'is_active', 'subscribed_at']


class BlogSubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subscriptions."""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = BlogSubscription
        fields = ['email', 'name', 'category_ids']

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        subscription = BlogSubscription.objects.create(**validated_data)

        if category_ids:
            categories = BlogCategory.objects.filter(id__in=category_ids, is_active=True)
            subscription.categories.add(*categories)

        return subscription
