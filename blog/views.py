"""
Blog App Views

API endpoints for educational blog/content functionality.
Full CRUD operations for posts, categories, tags, comments, and media.
"""
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
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
from .serializers import (
    BlogCategoryListSerializer,
    BlogCategoryDetailSerializer,
    BlogCategoryCreateUpdateSerializer,
    BlogTagSerializer,
    NewsSourceListSerializer,
    NewsSourceDetailSerializer,
    NewsSourceCreateUpdateSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateSerializer,
    BlogPostUpdateSerializer,
    BlogImageSerializer,
    BlogImageUploadSerializer,
    BlogCommentSerializer,
    BlogCommentCreateSerializer,
    BlogSubscriptionSerializer,
    BlogSubscriptionCreateSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for blog listings."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


def paginate_queryset(queryset, request, serializer_class):
    """Helper function to paginate querysets."""
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)

    if page is not None:
        serializer = serializer_class(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ============================================================
# CATEGORY ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog Categories'],
    summary='List all blog categories',
    description='Get all active blog categories with post counts.',
    operation_id='blog_categories_list_all',
    parameters=[
        OpenApiParameter(
            name='include_inactive',
            type=bool,
            description='Include inactive categories (admin only)',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=BlogCategoryListSerializer(many=True),
            description='List of categories'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_categories(request):
    """List all blog categories."""
    queryset = BlogCategory.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__status='published', posts__is_deleted=False))
    )

    include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'
    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    serializer = BlogCategoryListSerializer(
        queryset,
        many=True,
        context={'request': request}
    )

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog Categories'],
    summary='Get category details',
    description='Get detailed information about a specific category.',
    operation_id='blog_categories_get_by_slug',
    responses={
        200: OpenApiResponse(response=BlogCategoryDetailSerializer),
        404: OpenApiResponse(description='Category not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_category(request, slug):
    """Get category details by slug."""
    category = get_object_or_404(BlogCategory, slug=slug)
    serializer = BlogCategoryDetailSerializer(category, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog Categories'],
    summary='Create a new category',
    description='Create a new blog category. Requires authentication.',
    request=BlogCategoryCreateUpdateSerializer,
    responses={
        201: OpenApiResponse(response=BlogCategoryDetailSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_category(request):
    """Create a new blog category."""
    serializer = BlogCategoryCreateUpdateSerializer(data=request.data)

    if serializer.is_valid():
        try:
            category = serializer.save()
            response_serializer = BlogCategoryDetailSerializer(
                category,
                context={'request': request}
            )

            return Response({
                'success': True,
                'message': 'Category created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'errors': {'detail': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog Categories'],
    summary='Update a category',
    description='Update an existing blog category.',
    request=BlogCategoryCreateUpdateSerializer,
    responses={
        200: OpenApiResponse(response=BlogCategoryDetailSerializer),
        404: OpenApiResponse(description='Category not found')
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_category(request, slug):
    """Update a blog category."""
    category = get_object_or_404(BlogCategory, slug=slug)
    serializer = BlogCategoryCreateUpdateSerializer(
        category,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        category = serializer.save()
        response_serializer = BlogCategoryDetailSerializer(
            category,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Category updated successfully',
            'data': response_serializer.data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog Categories'],
    summary='Delete a category',
    description='Delete a blog category. Posts in this category will be uncategorized.',
    responses={
        200: OpenApiResponse(description='Category deleted'),
        404: OpenApiResponse(description='Category not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def delete_category(request, slug):
    """Delete a blog category."""
    category = get_object_or_404(BlogCategory, slug=slug)
    category.delete()

    return Response({
        'success': True,
        'message': 'Category deleted successfully'
    })


# ============================================================
# TAG ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog'],
    summary='List all tags',
    description='Get all blog tags with post counts.',
    operation_id='blog_tags_list_all',
    responses={
        200: OpenApiResponse(
            response=BlogTagSerializer(many=True),
            description='List of tags'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_tags(request):
    """List all blog tags."""
    queryset = BlogTag.objects.all()
    serializer = BlogTagSerializer(queryset, many=True, context={'request': request})

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog'],
    summary='Create a new tag',
    description='Create a new blog tag.',
    request=BlogTagSerializer,
    responses={
        201: OpenApiResponse(response=BlogTagSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def create_tag(request):
    """Create a new blog tag."""
    serializer = BlogTagSerializer(data=request.data)

    if serializer.is_valid():
        tag = serializer.save()
        return Response({
            'success': True,
            'message': 'Tag created successfully',
            'data': BlogTagSerializer(tag).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog'],
    summary='Get tag details',
    description='Get details of a specific tag by slug.',
    operation_id='blog_tags_get_by_slug',
    responses={
        200: OpenApiResponse(response=BlogTagSerializer),
        404: OpenApiResponse(description='Tag not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_tag(request, slug):
    """Get tag details by slug."""
    tag = get_object_or_404(BlogTag, slug=slug)
    serializer = BlogTagSerializer(tag, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog'],
    summary='Update a tag',
    description='Update a blog tag.',
    request=BlogTagSerializer,
    responses={
        200: OpenApiResponse(response=BlogTagSerializer),
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='Tag not found')
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def update_tag(request, slug):
    """Update a blog tag."""
    tag = get_object_or_404(BlogTag, slug=slug)
    serializer = BlogTagSerializer(tag, data=request.data, partial=True)

    if serializer.is_valid():
        tag = serializer.save()
        return Response({
            'success': True,
            'message': 'Tag updated successfully',
            'data': BlogTagSerializer(tag).data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog'],
    summary='Delete a tag',
    description='Delete a blog tag.',
    responses={
        200: OpenApiResponse(description='Tag deleted'),
        404: OpenApiResponse(description='Tag not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def delete_tag(request, slug):
    """Delete a blog tag."""
    tag = get_object_or_404(BlogTag, slug=slug)
    tag.delete()

    return Response({
        'success': True,
        'message': 'Tag deleted successfully'
    })


# ============================================================
# NEWS SOURCE ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog - News Sources'],
    summary='List all news sources',
    description='Get all active news sources for blog posts. Sources like BBC, CNN, Reuters add authenticity to content.',
    operation_id='blog_sources_list_all',
    parameters=[
        OpenApiParameter(
            name='include_inactive',
            type=bool,
            description='Include inactive sources (admin only)',
            required=False
        ),
        OpenApiParameter(
            name='verified_only',
            type=bool,
            description='Show only verified sources',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=NewsSourceListSerializer(many=True),
            description='List of news sources'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_sources(request):
    """List all news sources."""
    queryset = NewsSource.objects.all()

    # Filter by active status
    include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'
    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    # Filter by verified status
    verified_only = request.query_params.get('verified_only', 'false').lower() == 'true'
    if verified_only:
        queryset = queryset.filter(is_verified=True)

    serializer = NewsSourceListSerializer(
        queryset,
        many=True,
        context={'request': request}
    )

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog - News Sources'],
    summary='Get news source details',
    description='Get detailed information about a specific news source.',
    operation_id='blog_sources_get_by_slug',
    responses={
        200: OpenApiResponse(response=NewsSourceDetailSerializer),
        404: OpenApiResponse(description='Source not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_source(request, slug):
    """Get news source details by slug."""
    source = get_object_or_404(NewsSource, slug=slug)
    serializer = NewsSourceDetailSerializer(source, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog - News Sources'],
    summary='Create a new news source',
    description='Create a new news source (e.g., BBC, CNN, Reuters). Requires admin access.',
    request=NewsSourceCreateUpdateSerializer,
    responses={
        201: OpenApiResponse(response=NewsSourceDetailSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_source(request):
    """Create a new news source."""
    serializer = NewsSourceCreateUpdateSerializer(data=request.data)

    if serializer.is_valid():
        try:
            source = serializer.save()
            return Response({
                'success': True,
                'message': 'News source created successfully',
                'data': NewsSourceDetailSerializer(source, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'errors': {'detail': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog - News Sources'],
    summary='Update a news source',
    description='Update an existing news source.',
    request=NewsSourceCreateUpdateSerializer,
    responses={
        200: OpenApiResponse(response=NewsSourceDetailSerializer),
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='Source not found')
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_source(request, slug):
    """Update a news source."""
    source = get_object_or_404(NewsSource, slug=slug)
    serializer = NewsSourceCreateUpdateSerializer(
        source,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():
        source = serializer.save()
        return Response({
            'success': True,
            'message': 'News source updated successfully',
            'data': NewsSourceDetailSerializer(source, context={'request': request}).data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog - News Sources'],
    summary='Delete a news source',
    description='Delete a news source. Posts using this source will have their source set to null.',
    responses={
        200: OpenApiResponse(description='Source deleted'),
        404: OpenApiResponse(description='Source not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def delete_source(request, slug):
    """Delete a news source."""
    source = get_object_or_404(NewsSource, slug=slug)
    source_name = source.name
    source.delete()

    return Response({
        'success': True,
        'message': f'News source "{source_name}" deleted successfully'
    })


@extend_schema(
    tags=['Blog - News Sources'],
    summary='Get posts by news source',
    description='Get all published posts from a specific news source.',
    operation_id='blog_sources_posts',
    parameters=[
        OpenApiParameter(name='page', type=int, description='Page number'),
        OpenApiParameter(name='page_size', type=int, description='Items per page'),
    ],
    responses={
        200: OpenApiResponse(response=BlogPostListSerializer(many=True)),
        404: OpenApiResponse(description='Source not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_source_posts(request, slug):
    """Get all posts from a specific news source."""
    source = get_object_or_404(NewsSource, slug=slug, is_active=True)

    queryset = BlogPost.objects.filter(
        source=source,
        status='published',
        is_deleted=False
    ).select_related('category', 'author', 'source').prefetch_related('tags')

    return paginate_queryset(queryset, request, BlogPostListSerializer)


# ============================================================
# POST ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog'],
    summary='List all blog posts',
    description='''
    Get paginated list of published blog posts.

    **Filtering options:**
    - `category`: Filter by category slug
    - `tag`: Filter by tag slug
    - `source`: Filter by news source slug (e.g., bbc, cnn)
    - `content_type`: Filter by content type (article, guide, news, etc.)
    - `search`: Full-text search in title, content, excerpt
    - `featured`: Get only featured posts
    - `author`: Filter by author ID

    **Sorting:**
    - `ordering`: Sort by field (e.g., `-published_at`, `view_count`, `-like_count`)
    ''',
    operation_id='blog_posts_list_all',
    parameters=[
        OpenApiParameter(name='category', type=str, description='Category slug'),
        OpenApiParameter(name='tag', type=str, description='Tag slug'),
        OpenApiParameter(name='source', type=str, description='News source slug'),
        OpenApiParameter(name='content_type', type=str, description='Content type'),
        OpenApiParameter(name='search', type=str, description='Search query'),
        OpenApiParameter(name='featured', type=bool, description='Featured posts only'),
        OpenApiParameter(name='author', type=int, description='Author ID'),
        OpenApiParameter(name='ordering', type=str, description='Sort field'),
        OpenApiParameter(name='page', type=int, description='Page number'),
        OpenApiParameter(name='page_size', type=int, description='Items per page'),
    ],
    responses={
        200: OpenApiResponse(
            response=BlogPostListSerializer(many=True),
            description='Paginated list of posts'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_posts(request):
    """List all published blog posts with filtering."""
    queryset = BlogPost.objects.filter(
        status='published',
        is_deleted=False,
        published_at__lte=timezone.now()
    )

    # Category filter
    category = request.query_params.get('category')
    if category:
        queryset = queryset.filter(category__slug=category)

    # Tag filter
    tag = request.query_params.get('tag')
    if tag:
        queryset = queryset.filter(tags__slug=tag)

    # Source filter
    source = request.query_params.get('source')
    if source:
        queryset = queryset.filter(source__slug=source)

    # Content type filter
    content_type = request.query_params.get('content_type')
    if content_type:
        queryset = queryset.filter(content_type=content_type)

    # Search
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(excerpt__icontains=search)
        )

    # Featured filter
    featured = request.query_params.get('featured')
    if featured and featured.lower() == 'true':
        queryset = queryset.filter(is_featured=True)

    # Author filter
    author = request.query_params.get('author')
    if author:
        queryset = queryset.filter(author_id=author)

    # Ordering
    ordering = request.query_params.get('ordering', '-published_at')
    if ordering in ['-published_at', 'published_at', '-view_count', 'view_count',
                    '-like_count', 'like_count', '-created_at', 'created_at']:
        queryset = queryset.order_by(ordering)

    return paginate_queryset(queryset, request, BlogPostListSerializer)


@extend_schema(
    tags=['Blog'],
    summary='Get post details',
    description='Get detailed information about a specific blog post. Increments view count.',
    operation_id='blog_posts_get_by_slug',
    responses={
        200: OpenApiResponse(response=BlogPostDetailSerializer),
        404: OpenApiResponse(description='Post not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_post(request, slug):
    """Get post details by slug. Increments view count."""
    post = get_object_or_404(
        BlogPost,
        slug=slug,
        is_deleted=False
    )

    # Check if published (allow preview for admin)
    if post.status != 'published':
        # In production, check if user is admin
        pass

    # Increment view count
    post.increment_view()

    serializer = BlogPostDetailSerializer(post, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog'],
    summary='Get post by UUID',
    description='Get blog post by its UUID (useful for previews/drafts).',
    responses={
        200: OpenApiResponse(response=BlogPostDetailSerializer),
        404: OpenApiResponse(description='Post not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_post_by_id(request, post_id):
    """Get post details by UUID."""
    post = get_object_or_404(BlogPost, post_id=post_id, is_deleted=False)
    serializer = BlogPostDetailSerializer(post, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog'],
    summary='Create a new blog post',
    description='''
    Create a new blog post. Requires authentication.

    **Content Types:**
    - article: Standard article
    - guide: Step-by-step guide
    - news: News/announcement
    - tips: Tips & tricks
    - interview: Interview content
    - case_study: Case study
    - video: Video content (with video_url)

    **Status:**
    - draft: Not visible to public
    - review: Under review
    - published: Visible to public
    - archived: Hidden from listings
    ''',
    request=BlogPostCreateSerializer,
    responses={
        201: OpenApiResponse(response=BlogPostDetailSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_post(request):
    """Create a new blog post."""
    serializer = BlogPostCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        try:
            post = serializer.save()
            response_serializer = BlogPostDetailSerializer(
                post,
                context={'request': request}
            )

            return Response({
                'success': True,
                'message': 'Post created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'errors': {'detail': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog'],
    summary='Update a blog post',
    description='Update an existing blog post.',
    request=BlogPostUpdateSerializer,
    responses={
        200: OpenApiResponse(response=BlogPostDetailSerializer),
        404: OpenApiResponse(description='Post not found')
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_post(request, slug):
    """Update an existing blog post."""
    post = get_object_or_404(BlogPost, slug=slug, is_deleted=False)

    serializer = BlogPostUpdateSerializer(
        post,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        post = serializer.save()
        response_serializer = BlogPostDetailSerializer(
            post,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Post updated successfully',
            'data': response_serializer.data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog'],
    summary='Delete a blog post',
    description='Soft delete a blog post. The post is not permanently removed.',
    responses={
        200: OpenApiResponse(description='Post deleted'),
        404: OpenApiResponse(description='Post not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def delete_post(request, slug):
    """Soft delete a blog post."""
    post = get_object_or_404(BlogPost, slug=slug, is_deleted=False)

    post.is_deleted = True
    post.deleted_at = timezone.now()
    post.save()

    return Response({
        'success': True,
        'message': 'Post deleted successfully'
    })


class LikePostRequestSerializer(serializers.Serializer):
    """Empty request body for like post action."""
    pass


class LikePostResponseSerializer(serializers.Serializer):
    """Response for like post action."""
    success = serializers.BooleanField()
    like_count = serializers.IntegerField()


@extend_schema(
    tags=['Blog'],
    summary='Like a blog post',
    description='Increment the like count for a post.',
    request=LikePostRequestSerializer,
    responses={
        200: LikePostResponseSerializer
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def like_post(request, slug):
    """Like a blog post."""
    post = get_object_or_404(BlogPost, slug=slug, is_deleted=False)
    post.like_count += 1
    post.save(update_fields=['like_count'])

    return Response({
        'success': True,
        'like_count': post.like_count
    })


# ============================================================
# IMAGE ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog'],
    summary='List uploaded images',
    description='Get list of uploaded images (media library).',
    operation_id='blog_images_list_all',
    responses={
        200: OpenApiResponse(
            response=BlogImageSerializer(many=True),
            description='List of images'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def list_images(request):
    """List all uploaded images."""
    queryset = BlogImage.objects.all()

    return paginate_queryset(queryset, request, BlogImageSerializer)


@extend_schema(
    tags=['Blog'],
    summary='Upload an image',
    description='''
    Upload an image to the media library.

    **Supported formats:** JPG, PNG, GIF, WebP
    **Max size:** 5MB (recommended)

    Images are stored in cloud storage (Cloudinary) if configured,
    otherwise stored locally.
    ''',
    request=BlogImageUploadSerializer,
    responses={
        201: OpenApiResponse(response=BlogImageSerializer),
        400: OpenApiResponse(description='Invalid image')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """Upload an image to the media library."""
    import cloudinary.uploader

    # Check if image file is provided
    if 'image' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No image file provided. Use form-data with key "image" and select a file.'
        }, status=status.HTTP_400_BAD_REQUEST)

    image_file = request.FILES['image']

    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        return Response({
            'success': False,
            'error': f'Invalid file type: {image_file.content_type}. Allowed: JPG, PNG, GIF, WebP'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if image_file.size > max_size:
        return Response({
            'success': False,
            'error': f'File too large: {image_file.size / 1024 / 1024:.2f}MB. Max: 10MB'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Read file content into memory
        image_file.seek(0)
        file_content = image_file.read()

        # Upload directly to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file_content,
            folder='blog/media',
            resource_type='image'
        )

        # Create BlogImage record with the Cloudinary URL
        title = request.data.get('title', '')
        alt_text = request.data.get('alt_text', '')
        caption = request.data.get('caption', '')

        image = BlogImage.objects.create(
            image=upload_result['public_id'],  # Store public_id for Cloudinary
            title=title or image_file.name,
            alt_text=alt_text,
            caption=caption,
            file_size=upload_result.get('bytes', 0),
            width=upload_result.get('width', 0),
            height=upload_result.get('height', 0),
            uploaded_by=request.user if request.user.is_authenticated else None
        )

        # Return response with Cloudinary URL
        return Response({
            'success': True,
            'message': 'Image uploaded successfully',
            'data': {
                'image_id': str(image.image_id),
                'title': image.title,
                'alt_text': image.alt_text,
                'caption': image.caption,
                'image_url': upload_result['secure_url'],
                'file_size': image.file_size,
                'width': image.width,
                'height': image.height,
                'created_at': image.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)

    except cloudinary.exceptions.Error as e:
        return Response({
            'success': False,
            'error': f'Cloudinary upload failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': f'Upload failed: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog'],
    summary='Get an image',
    description='Get details of a specific image from the media library.',
    operation_id='blog_images_get_by_id',
    responses={
        200: BlogImageSerializer,
        404: OpenApiResponse(description='Image not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_image(request, image_id):
    """Get a specific image by ID."""
    image = get_object_or_404(BlogImage, image_id=image_id)
    serializer = BlogImageSerializer(image, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog'],
    summary='Delete an image',
    description='Delete an image from the media library.',
    responses={
        200: OpenApiResponse(description='Image deleted'),
        404: OpenApiResponse(description='Image not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def delete_image(request, image_id):
    """Delete an image."""
    image = get_object_or_404(BlogImage, image_id=image_id)

    # Delete the file too
    if image.image:
        image.image.delete(save=False)

    image.delete()

    return Response({
        'success': True,
        'message': 'Image deleted successfully'
    })


# ============================================================
# COMMENT ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog Comments'],
    summary='List comments for a post',
    description='Get all approved comments for a blog post.',
    responses={
        200: OpenApiResponse(
            response=BlogCommentSerializer(many=True),
            description='List of comments'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_post_comments(request, slug):
    """List approved comments for a post."""
    post = get_object_or_404(BlogPost, slug=slug, is_deleted=False)

    # Get only top-level approved comments
    comments = BlogComment.objects.filter(
        post=post,
        status='approved',
        parent__isnull=True
    )

    serializer = BlogCommentSerializer(
        comments,
        many=True,
        context={'request': request}
    )

    return Response({
        'success': True,
        'count': comments.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Blog Comments'],
    summary='Add a comment',
    description='''
    Add a comment to a blog post.

    **Guest comments:** Provide guest_name and guest_email
    **Authenticated comments:** No guest info needed

    Comments are held for moderation by default.
    ''',
    request=BlogCommentCreateSerializer,
    responses={
        201: OpenApiResponse(response=BlogCommentSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_comment(request, slug):
    """Add a comment to a post."""
    post = get_object_or_404(BlogPost, slug=slug, is_deleted=False)

    if not post.allow_comments:
        return Response({
            'success': False,
            'error': 'Comments are disabled for this post'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()
    data['post'] = post.id

    serializer = BlogCommentCreateSerializer(
        data=data,
        context={'request': request}
    )

    if serializer.is_valid():
        comment = serializer.save(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )

        # Auto-approve authenticated users (optional)
        if request.user.is_authenticated:
            comment.status = 'approved'
            comment.save()

        response_serializer = BlogCommentSerializer(
            comment,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Comment submitted successfully. It will appear after moderation.',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Blog Comments'],
    summary='Delete a comment',
    description='Delete a comment. Admin only.',
    responses={
        200: OpenApiResponse(description='Comment deleted'),
        404: OpenApiResponse(description='Comment not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def delete_comment(request, comment_id):
    """Delete a comment."""
    comment = get_object_or_404(BlogComment, comment_id=comment_id)
    comment.delete()

    return Response({
        'success': True,
        'message': 'Comment deleted successfully'
    })


@extend_schema(
    tags=['Blog Comments'],
    summary='Moderate a comment (Admin)',
    description='Approve, reject, or mark comment as spam.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'enum': ['approved', 'rejected', 'spam']},
                'is_highlighted': {'type': 'boolean'}
            }
        }
    },
    responses={
        200: OpenApiResponse(description='Comment moderated')
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def moderate_comment(request, comment_id):
    """Moderate a comment."""
    comment = get_object_or_404(BlogComment, comment_id=comment_id)

    new_status = request.data.get('status')
    if new_status in ['approved', 'rejected', 'spam', 'pending']:
        comment.status = new_status

    is_highlighted = request.data.get('is_highlighted')
    if is_highlighted is not None:
        comment.is_highlighted = is_highlighted

    comment.save()

    return Response({
        'success': True,
        'message': f'Comment status updated to {comment.status}'
    })


# ============================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Blog'],
    summary='Subscribe to blog updates',
    description='Subscribe to receive email notifications for new posts.',
    request=BlogSubscriptionCreateSerializer,
    responses={
        201: OpenApiResponse(response=BlogSubscriptionSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def subscribe(request):
    """Subscribe to blog updates."""
    serializer = BlogSubscriptionCreateSerializer(data=request.data)

    if serializer.is_valid():
        # Check if already subscribed
        email = serializer.validated_data['email']
        existing = BlogSubscription.objects.filter(email__iexact=email).first()

        if existing:
            if existing.is_active:
                return Response({
                    'success': False,
                    'error': 'This email is already subscribed'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Reactivate
                existing.is_active = True
                existing.unsubscribed_at = None
                existing.save()

                return Response({
                    'success': True,
                    'message': 'Subscription reactivated successfully'
                })

        subscription = serializer.save()

        # TODO: Send verification email
        # send_subscription_verification_email(subscription)

        response_serializer = BlogSubscriptionSerializer(subscription)

        return Response({
            'success': True,
            'message': 'Subscribed successfully. Please check your email to verify.',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeRequestSerializer(serializers.Serializer):
    """Request body for unsubscribe action."""
    email = serializers.EmailField(required=True, help_text="Email address to unsubscribe")


class UnsubscribeResponseSerializer(serializers.Serializer):
    """Response for unsubscribe action."""
    success = serializers.BooleanField()
    message = serializers.CharField()


@extend_schema(
    tags=['Blog'],
    summary='Unsubscribe from blog updates',
    description='Unsubscribe from email notifications.',
    request=UnsubscribeRequestSerializer,
    responses={
        200: UnsubscribeResponseSerializer,
        404: OpenApiResponse(description='Subscription not found')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def unsubscribe(request):
    """Unsubscribe from blog updates."""
    email = request.data.get('email')

    if not email:
        return Response({
            'success': False,
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    subscription = get_object_or_404(BlogSubscription, email__iexact=email)

    subscription.is_active = False
    subscription.unsubscribed_at = timezone.now()
    subscription.save()

    return Response({
        'success': True,
        'message': 'Unsubscribed successfully'
    })


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin'],
    summary='List all posts (Admin)',
    description='Get all posts including drafts and archived. Admin only.',
    parameters=[
        OpenApiParameter(name='status', type=str, description='Filter by status'),
        OpenApiParameter(name='author', type=int, description='Filter by author ID'),
    ],
    responses={
        200: OpenApiResponse(
            response=BlogPostListSerializer(many=True),
            description='All posts'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def admin_list_posts(request):
    """Admin: List all posts including drafts."""
    queryset = BlogPost.objects.filter(is_deleted=False)

    # Status filter
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Author filter
    author = request.query_params.get('author')
    if author:
        queryset = queryset.filter(author_id=author)

    return paginate_queryset(queryset, request, BlogPostListSerializer)


@extend_schema(
    tags=['Admin'],
    summary='Blog statistics',
    description='Get blog statistics for dashboard.',
    responses={
        200: OpenApiResponse(
            description='Blog statistics',
            examples=[
                OpenApiExample(
                    'Stats',
                    value={
                        'total_posts': 50,
                        'published': 40,
                        'drafts': 8,
                        'archived': 2,
                        'total_views': 15000,
                        'total_comments': 200,
                        'pending_comments': 5
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def blog_stats(request):
    """Get blog statistics."""
    stats = {
        'total_posts': BlogPost.objects.filter(is_deleted=False).count(),
        'published': BlogPost.objects.filter(status='published', is_deleted=False).count(),
        'drafts': BlogPost.objects.filter(status='draft', is_deleted=False).count(),
        'archived': BlogPost.objects.filter(status='archived', is_deleted=False).count(),
        'total_views': BlogPost.objects.filter(is_deleted=False).aggregate(
            total=Sum('view_count')
        )['total'] or 0,
        'total_likes': BlogPost.objects.filter(is_deleted=False).aggregate(
            total=Sum('like_count')
        )['total'] or 0,
        'total_comments': BlogComment.objects.count(),
        'pending_comments': BlogComment.objects.filter(status='pending').count(),
        'total_categories': BlogCategory.objects.filter(is_active=True).count(),
        'total_tags': BlogTag.objects.count(),
        'total_subscribers': BlogSubscription.objects.filter(is_active=True).count(),
    }

    return Response({
        'success': True,
        'data': stats
    })
