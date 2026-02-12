"""
WebSocket Consumers for Mole-AI Real-time Chat System
"""
import json
import logging
from typing import Optional
from asyncio import sleep
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

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
            
            # Process with enhanced AI service (in database_sync_to_async for DB access)
            if get_enhanced_ai_response:
                response_data = await database_sync_to_async(self._process_with_ai)(
                    question=question,
                    plant_id=data.get('plant_id'),
                    user_id=self.user_id,
                    session_id=self.session_id
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
    
    def _process_with_ai(self, question: str, plant_id: Optional[str] = None, 
                       user_id: Optional[int] = None, session_id: Optional[str] = None) -> dict:
        """
        Process user query with Mole-AI enhanced service
        This runs in database_sync_to_async context
        """
        try:
            return get_enhanced_ai_response(
                query=question,
                plant_id=plant_id,
                user_id=user_id or -1,  # Use -1 para usuarios anónimos
                session_id=session_id or f"anonymous_{id(self)}",
                context=None,  # Can be enhanced with RAG in future
                max_tokens=1024,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"AI processing error: {str(e)}")
            raise e
    
    async def send_json(self, data: dict):
        """Send JSON message through WebSocket"""
        await self.send(text_data=json.dumps(data))