from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def llm_requests_view(request):
    """
    API endpoint para gestionar peticiones LLM
    """
    return Response({
        'message': 'LLM Requests - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cnn_inferences_view(request):
    """
    API endpoint para gestionar inferencias CNN
    """
    return Response({
        'message': 'CNN Inferences - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_performance_view(request):
    """
    API endpoint para métricas de rendimiento de modelos
    """
    return Response({
        'message': 'Model Performance - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_model_config_view(request):
    """
    API endpoint para configuración de modelos IA
    """
    return Response({
        'message': 'AI Model Configuration - Endpoint placeholder',
        'status': 'implemented',
        'app': 'ai_models'
    })


class AIHealthCheckView(APIView):
    """
    Health check para el módulo de IA
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'AI Models Module',
            'version': '1.0.0'
        })