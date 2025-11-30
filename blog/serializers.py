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

class BlogCommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments."""
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
        if obj.replies.exists():
            return BlogCommentSerializer(
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
            'category', 'tags', 'author', 'status', 'published_at',
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
            'category', 'tags', 'tag_ids', 'status', 'published_at',
            'is_featured', 'is_pinned', 'allow_comments',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url'
        ]
        extra_kwargs = {
            'slug': {'required': False},
            'excerpt': {'required': False}
        }

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
            'category', 'tags', 'tag_ids', 'status', 'published_at',
            'is_featured', 'is_pinned', 'allow_comments',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url'
        ]

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
