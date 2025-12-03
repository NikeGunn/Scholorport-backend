"""
Partners App Views

API endpoints for partner management.
Public endpoints for homepage display, admin endpoints for CRUD operations.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Partner
from .serializers import PartnerListSerializer, PartnerAdminSerializer


# ============================================================
# PUBLIC ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Partners'],
    summary='List all active partners',
    description='''
    Get a list of all active partners for display on the homepage.
    No authentication required.

    Supports filtering by:
    - type: 'university' or 'agent'
    - featured: true/false
    ''',
    parameters=[
        OpenApiParameter(
            name='type',
            type=str,
            description="Filter by partner type ('university' or 'agent')",
            required=False
        ),
        OpenApiParameter(
            name='featured',
            type=bool,
            description='Filter featured partners only',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=PartnerListSerializer(many=True),
            description='List of partners'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_partners(request):
    """List all active partners (public endpoint)."""
    queryset = Partner.objects.filter(is_active=True)

    # Filter by type
    partner_type = request.query_params.get('type')
    if partner_type in ['university', 'agent']:
        queryset = queryset.filter(type=partner_type)

    # Filter by featured
    featured = request.query_params.get('featured')
    if featured is not None:
        if featured.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(featured=True)
        elif featured.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(featured=False)

    serializer = PartnerListSerializer(
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
    tags=['Partners'],
    summary='Get partner details',
    description='Get details of a specific partner.',
    responses={
        200: OpenApiResponse(
            response=PartnerListSerializer,
            description='Partner details'
        ),
        404: OpenApiResponse(description='Partner not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_partner(request, partner_id):
    """Get details of a specific partner."""
    partner = get_object_or_404(Partner, id=partner_id, is_active=True)
    serializer = PartnerListSerializer(partner, context={'request': request})

    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin - Partners'],
    summary='List all partners (Admin)',
    description='Get all partners including inactive ones. Requires admin authentication.',
    responses={
        200: OpenApiResponse(
            response=PartnerAdminSerializer(many=True),
            description='List of all partners'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_partners(request):
    """Admin: List all partners including inactive."""
    queryset = Partner.objects.all()

    # Filter by type
    partner_type = request.query_params.get('type')
    if partner_type in ['university', 'agent']:
        queryset = queryset.filter(type=partner_type)

    # Filter by active status
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        if is_active.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(is_active=True)
        elif is_active.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(is_active=False)

    serializer = PartnerAdminSerializer(
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
    tags=['Admin - Partners'],
    summary='Create a partner (Admin)',
    description='Create a new partner. Requires admin authentication.',
    request=PartnerAdminSerializer,
    responses={
        201: OpenApiResponse(
            response=PartnerAdminSerializer,
            description='Partner created successfully'
        ),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_partner(request):
    """Admin: Create a new partner."""
    serializer = PartnerAdminSerializer(data=request.data)

    if serializer.is_valid():
        partner = serializer.save()
        return Response({
            'success': True,
            'message': 'Partner created successfully',
            'data': PartnerAdminSerializer(partner, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin - Partners'],
    summary='Update a partner (Admin)',
    description='Update an existing partner. Requires admin authentication.',
    request=PartnerAdminSerializer,
    responses={
        200: OpenApiResponse(
            response=PartnerAdminSerializer,
            description='Partner updated successfully'
        ),
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='Partner not found')
    }
)
@api_view(['PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_update_partner(request, partner_id):
    """Admin: Update a partner."""
    partner = get_object_or_404(Partner, id=partner_id)
    serializer = PartnerAdminSerializer(
        partner,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Partner updated successfully',
            'data': serializer.data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin - Partners'],
    summary='Delete a partner (Admin)',
    description='Delete a partner. Requires admin authentication.',
    responses={
        200: OpenApiResponse(description='Partner deleted successfully'),
        404: OpenApiResponse(description='Partner not found')
    }
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_partner(request, partner_id):
    """Admin: Delete a partner."""
    partner = get_object_or_404(Partner, id=partner_id)
    partner_name = partner.name
    partner.delete()

    return Response({
        'success': True,
        'message': f'Partner "{partner_name}" deleted successfully'
    })
