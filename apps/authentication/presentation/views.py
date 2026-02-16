from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    API endpoint para obtener el perfil del usuario
    """
    return Response({
        'message': 'User Profile - Endpoint placeholder',
        'status': 'implemented',
        'app': 'authentication',
        'user_id': request.user.id if request.user.is_authenticated else None
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_subscription_view(request):
    """
    API endpoint para gestionar suscripciones de usuario
    """
    if request.method == 'GET':
        return Response({
            'message': 'Get User Subscription - Endpoint placeholder',
            'status': 'implemented',
            'app': 'authentication'
        })
    elif request.method == 'PUT':
        return Response({
            'message': 'Update User Subscription - Endpoint placeholder',
            'status': 'implemented',
            'app': 'authentication'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_metadata_view(request):
    """
    API endpoint para metadatos de Supabase del usuario
    """
    return Response({
        'message': 'User Metadata - Endpoint placeholder',
        'status': 'implemented',
        'app': 'authentication',
        'supabase_uid': getattr(request.user, 'supabase_uid', None) if request.user.is_authenticated else None
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    API endpoint para logout personalizado
    """
    return Response({
        'message': 'Logout - Endpoint placeholder',
        'status': 'implemented',
        'app': 'authentication'
    })


class AuthHealthCheckView(APIView):
    """
    Health check para el módulo de autenticación
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Authentication Module',
            'version': '1.0.0'
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_debug_view(request):
    """
    Debug endpoint for Auth headers
    """
    return Response({
        'user': str(request.user),
        'auth_header': request.META.get('HTTP_AUTHORIZATION', 'None'),
        'is_authenticated': request.user.is_authenticated,
        'supabase_uid': getattr(request.user, 'supabase_uid', None)
    })