"""
Blog App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # ==================== Category Endpoints ====================
    # List all categories
    path('categories/', views.list_categories, name='list-categories'),

    # Create category
    path('categories/create/', views.create_category, name='create-category'),

    # Get/Update/Delete category by ID
    path('categories/<int:pk>/', views.get_category_by_id, name='get-category-by-id'),
    path('categories/<int:pk>/update/', views.update_category_by_id, name='update-category-by-id'),
    path('categories/<int:pk>/delete/', views.delete_category_by_id, name='delete-category-by-id'),

    # Get/Update/Delete category by slug
    path('categories/<slug:slug>/', views.get_category, name='get-category'),
    path('categories/<slug:slug>/update/', views.update_category, name='update-category'),
    path('categories/<slug:slug>/delete/', views.delete_category, name='delete-category'),

    # ==================== Tag Endpoints ====================
    # List all tags
    path('tags/', views.list_tags, name='list-tags'),

    # Create tag
    path('tags/create/', views.create_tag, name='create-tag'),

    # Get tag details
    path('tags/<slug:slug>/', views.get_tag, name='get-tag'),

    # Update tag
    path('tags/<slug:slug>/update/', views.update_tag, name='update-tag'),

    # Delete tag
    path('tags/<slug:slug>/delete/', views.delete_tag, name='delete-tag'),

    # ==================== News Source Endpoints ====================
    # List all sources
    path('sources/', views.list_sources, name='list-sources'),

    # Create source
    path('sources/create/', views.create_source, name='create-source'),

    # Get source details
    path('sources/<slug:slug>/', views.get_source, name='get-source'),

    # Update source
    path('sources/<slug:slug>/update/', views.update_source, name='update-source'),

    # Delete source
    path('sources/<slug:slug>/delete/', views.delete_source, name='delete-source'),

    # Get posts by source
    path('sources/<slug:slug>/posts/', views.get_source_posts, name='source-posts'),

    # ==================== Post Endpoints ====================
    # List posts (public, published only)
    path('posts/', views.list_posts, name='list-posts'),

    # Create post
    path('posts/create/', views.create_post, name='create-post'),

    # Get post by UUID (for previews)
    path('posts/id/<uuid:post_id>/', views.get_post_by_id, name='get-post-by-id'),

    # Get/Update/Delete post by slug
    path('posts/<slug:slug>/', views.get_post, name='get-post'),
    path('posts/<slug:slug>/update/', views.update_post, name='update-post'),
    path('posts/<slug:slug>/delete/', views.delete_post, name='delete-post'),

    # Like post
    path('posts/<slug:slug>/like/', views.like_post, name='like-post'),

    # ==================== Image Endpoints ====================
    # List images (media library)
    path('images/', views.list_images, name='list-images'),

    # Upload image
    path('images/upload/', views.upload_image, name='upload-image'),

    # Get single image
    path('images/<uuid:image_id>/', views.get_image, name='get-image'),

    # Delete image
    path('images/<uuid:image_id>/delete/', views.delete_image, name='delete-image'),

    # ==================== Comment Endpoints ====================
    # List comments for a post
    path('posts/<slug:slug>/comments/', views.list_post_comments, name='list-comments'),

    # Create comment
    path('posts/<slug:slug>/comments/create/', views.create_comment, name='create-comment'),

    # Delete comment (admin)
    path('comments/<uuid:comment_id>/delete/', views.delete_comment, name='delete-comment'),

    # Moderate comment (admin)
    path('comments/<uuid:comment_id>/moderate/', views.moderate_comment, name='moderate-comment'),

    # ==================== Subscription Endpoints ====================
    # Subscribe
    path('subscribe/', views.subscribe, name='subscribe'),

    # Unsubscribe
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),

    # ==================== Admin Endpoints ====================
    # List all posts (admin)
    path('admin/posts/', views.admin_list_posts, name='admin-list-posts'),

    # Blog statistics
    path('admin/stats/', views.blog_stats, name='blog-stats'),
]
