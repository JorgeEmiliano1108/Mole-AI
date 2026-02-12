"""
WebSocket routing for Mole-AI chat system
"""
from django.urls import re_path
from .consumers import ChatConsumer

# WebSocket URL patterns for Channels routing
websocket_urlpatterns = [
    re_path(r'ws/chat/$', ChatConsumer.as_asgi()),
]