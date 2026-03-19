# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
WebSocket Consumers for Mole-AI Real-time Chat System
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
# channels.db.database_sync_to_async removed: using async MoleAI client instead

# Import con manejo de errores
try:
    from ai_models.services import get_enhanced_ai_response
except ImportError as e:
    print(f"⚠️ No se puede importar AI services: {e}")
    get_enhanced_ai_response = None

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat with Mole-AI integration
    Handles user connections and message processing with sensor data
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        
        # Get user from scope
        user = self.scope.get("user", None)
        self.user_id = user.id if user and hasattr(user, 'is_authenticated') and user.is_authenticated else None
        self.session_id = self.scope.get("session", {}).get("session_key", f"anonymous_{id(self)}")
        
        logger.info(f"WebSocket connected: user_id={self.user_id}, session_id={self.session_id}")
        
        # Send welcome message
        await self.send_json({
            "type": "connection",
            "message": "🤖 Conectado a Mole-AI. Envía tu consulta agrícola...",
            "status": "connected"
        })
    
    async def disconnect(self, code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected: user_id={self.user_id}, code={code}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages
        Process user queries and send to Mole-AI service
        """
        try:
            # Use text_data for string messages (backwards compatibility)
            message_content = text_data or (bytes_data.decode('utf-8') if bytes_data else None)
            
            if not message_content:
                await self.send_json({
                    "type": "error",
                    "message": "❌ Mensaje vacío no permitido."
                })
                return
            
            data = json.loads(message_content)
            logger.info(f"Received message from user {self.user_id}: {str(data)[:100]}...")
            
            # Validate required fields
            question = data.get('question', '').strip()
            if not question:
                await self.send_json({
                    "type": "error",
                    "message": "❌ Por favor, escribe una pregunta válida."
                })
                return
            
            # Send processing status
            await self.send_json({
                "type": "status",
                "message": "🤖 Mole-AI procesando tu consulta...",
                "processing": True
            })
            
            # Process with enhanced AI service (async)
            image_base64 = data.get('image_base64')
            if get_enhanced_ai_response:
                response_data = await get_enhanced_ai_response(
                    query=question,
                    plant_id=data.get('plant_id'),
                    user_id=self.user_id,
                    session_id=self.session_id,
                    context=None,
                    max_tokens=1024,
                    temperature=0.7,
                    image_base64=image_base64
                )
                
                # Send AI response
                await self.send_json({
                    "type": "response",
                    "answer": response_data['answer'],
                    "model_used": response_data['model_used'],
                    "tokens_generated": response_data['tokens_generated'],
                    "tactical_alerts_count": response_data.get('tactical_alerts_count', 0),
                    "processing_time_ms": response_data['processing_time_ms'],
                    "request_id": response_data.get('request_id')
                })
                
                logger.info(f"Mole-AI response sent: {response_data['processing_time_ms']}ms, {response_data.get('tactical_alerts_count', 0)} alerts")
            else:
                await self.send_json({
                    "type": "error",
                    "message": "❌ Servicio IA no disponible"
                })
            
        except json.JSONDecodeError:
            await self.send_json({
                "type": "error",
                "message": "❌ Formato de mensaje inválido. Usa JSON válido."
            })
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_json({
                "type": "error",
                "message": f"❌ Error en Mole-AI: {str(e)}"
            })
    
    # Removed _process_with_ai sync wrapper; using async get_enhanced_ai_response directly
    
    async def send_json(self, data: dict):
        """Send JSON message through WebSocket"""
        await self.send(text_data=json.dumps(data))