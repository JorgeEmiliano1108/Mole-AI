"""
Infrastructure AI - LLM Implementation (Phi-3.5)
(CORREGIDO: Flash Attention desactivado y uso de AutoProcessor)
"""
import logging
import time
import asyncio
from typing import List, Optional
import os
import base64

import torch
import psutil
from transformers import AutoModelForCausalLM, AutoProcessor
from huggingface_hub import InferenceClient

from domain.models import ChatRequest, ChatResponse, ModelStatus, ModelType, SensorData
from domain.ports import LLMGenerationPort

logger = logging.getLogger(__name__)

# MAPPER EXPLICITO (FIX AUDITORIA)
MODEL_ID_MAP = {
    ModelType.SENTENCE_TRANSFORMER: "sentence-transformers/all-mpnet-base-v2",
    ModelType.PHI35_VISION: "Qwen/Qwen2.5-VL-7B-Instruct"
}

class Phi35LLMAdapter(LLMGenerationPort):
    """Implementation of LLMGenerationPort using Phi-3.5 with Multimodal Support"""

    def __init__(self, model_name: str = None):
        self.model_type = model_name or ModelType.PHI35_VISION
        env_override = os.getenv("LLM_MODEL_ID")
        if isinstance(env_override, str) and env_override.strip():
            self.model_id = env_override
        else:
            self.model_id = MODEL_ID_MAP.get(
                self.model_type,
                self.model_type.value if hasattr(self.model_type, 'value') else str(self.model_type)
            )
        if not isinstance(self.model_id, str):
            raise TypeError(f"model_id must be string, got {type(self.model_id)}")
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        self.loading_time_ms = None
        self.memory_usage_mb = None
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.use_api = bool(self.hf_api_key)
        if self.use_api:
            self.client = InferenceClient(model=self.model_id, token=self.hf_api_key)
            logger.info(f"LLM adapter initialized with HF API for model: {self.model_id}")
        else:
            logger.info(f"LLM adapter initialized for local model: {self.model_id}")

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate text response using LLM with context and optional image"""
        if self.use_api:
            return await self._generate_response_api(request)
        else:
            if not self.is_loaded:
                await self.load_model()
            return await self._generate_response_local(request)

    async def _generate_response_local(self, request: ChatRequest) -> ChatResponse:
        """Generate response using local model"""
        try:
            prompt = self._create_prompt(
                query=request.query,
                context=request.context or [],
                sensor_data=request.sensor_data
            )
            response_text = await self._generate_text_async(
                prompt=prompt,
                image_data=request.image,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            tokens_count = len(response_text.split()) * 1.3
            return ChatResponse(
                answer=response_text.strip(),
                model_used=self.model_id,
                tokens_generated=int(tokens_count)
            )
        except Exception as e:
            logger.error(f"Error generating local LLM response: {str(e)}")
            raise

    async def _generate_response_api(self, request: ChatRequest) -> ChatResponse:
        """
        Generate response using HuggingFace Router API (OpenAI-compatible).
        Supports multimodal (text + image) when request.image is provided.
        Uses https://router.huggingface.co/v1/chat/completions
        """
        import aiohttp
        try:
            start = time.time()
            prompt = self._create_prompt(
                query=request.query,
                context=request.context or [],
                sensor_data=request.sensor_data
            )

            # Split prompt into system and user parts for proper message roles
            system_prompt, user_prompt = self._split_prompt(prompt)

            # Build messages array with proper roles
            if request.image:
                # Multimodal: user content is array with text + image
                image_url = request.image
                # Ensure proper data URI format for base64 images
                if not image_url.startswith("http") and not image_url.startswith("data:"):
                    image_url = f"data:image/jpeg;base64,{image_url}"
                
                user_content = [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
                logger.info("Building multimodal request with image for vision analysis")
            else:
                user_content = user_prompt

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # OpenAI-compatible chat completions format
            api_url = "https://router.huggingface.co/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": request.max_tokens or 1024,
                "temperature": request.temperature or 0.7,
                "stream": False,
            }
            logger.info(f"Calling HF Router API for model: {self.model_id} (multimodal={bool(request.image)})")
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    # Handle non-JSON responses
                    content_type = resp.content_type or ""
                    if "json" not in content_type:
                        text = await resp.text()
                        logger.error(f"HF API returned non-JSON ({resp.status}): {text[:500]}")
                        raise RuntimeError(f"HF API returned {resp.status}: {text[:200]}")
                    result = await resp.json()
                    logger.info(f"HF API status: {resp.status}, response: {str(result)[:500]}")
                    if resp.status != 200:
                        err = result.get("error", result) if isinstance(result, dict) else result
                        error_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                        raise RuntimeError(f"HF API returned {resp.status}: {error_msg}")
            # Parse OpenAI-compatible response
            response_text = ""
            if isinstance(result, dict):
                choices = result.get("choices", [])
                if choices and len(choices) > 0:
                    msg = choices[0].get("message", {})
                    response_text = msg.get("content", "")
                else:
                    response_text = str(result)
            else:
                response_text = str(result)
            elapsed_ms = int((time.time() - start) * 1000)
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            tokens_count = usage.get("completion_tokens", len(response_text.split()))
            logger.info(f"HF API response in {elapsed_ms}ms ({tokens_count} tokens)")
            return ChatResponse(
                answer=response_text.strip(),
                model_used=self.model_id + " (API)",
                tokens_generated=int(tokens_count),
                processing_time_ms=elapsed_ms
            )
        except aiohttp.ClientError as e:
            logger.error(f"HF API connection error: {str(e)}")
            raise RuntimeError(f"HuggingFace API connection error: {str(e)}")
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"HF API error: {str(e)}", exc_info=True)
            raise RuntimeError(f"HuggingFace API error: {str(e)}")

    async def get_model_status(self) -> ModelStatus:
        """Get current model status safely"""
        if self.is_loaded:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_usage_mb = round(memory_mb, 2)
            except Exception as e:
                logger.warning(f"Could not retrieve memory usage: {e}")
                self.memory_usage_mb = None
        return ModelStatus(
            model=self.model_id,
            is_loaded=self.is_loaded or self.use_api,
            loading_time_ms=self.loading_time_ms,
            memory_usage_mb=self.memory_usage_mb
        )

    async def load_model(self) -> None:
        """Load the LLM model (called once at startup)"""
        if self.use_api:
            self.is_loaded = True
            return
        if self.is_loaded:
            return
        try:
            start_time = time.time()
            logger.info(f"Loading LLM model: {self.model_id} on {self.device}...")
            self.processor = await asyncio.to_thread(
                AutoProcessor.from_pretrained,
                self.model_id,
                trust_remote_code=True
            )
            torch_dtype = "auto" if self.device == "cuda" else torch.float32
            self.model = await asyncio.to_thread(
                AutoModelForCausalLM.from_pretrained,
                self.model_id,
                device_map=self.device,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                _attn_implementation='eager'
            )
            self.is_loaded = True
            self.loading_time_ms = (time.time() - start_time) * 1000
            logger.info(f"LLM model loaded in {self.loading_time_ms:.2f}ms")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {str(e)}", exc_info=True)
            raise

    async def unload_model(self) -> None:
        """Unload the model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.processor:
                del self.processor
                self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.is_loaded = False
            logger.info("LLM model unloaded")
        except Exception as e:
            logger.error(f"Error unloading model: {str(e)}")

    def _create_prompt(self, query: str, context: List[str], sensor_data: SensorData = None) -> str:
        """Create a prompt using the domain PromptBuilder."""
        from domain.services.prompt_builder import PromptBuilder
        return PromptBuilder.build_chat_prompt(
            query=query,
            context=context if context else None,
            sensor_data=sensor_data,
        )

    def _split_prompt(self, prompt: str) -> tuple:
        """Split composed prompt into system and user parts for role-based messaging.
        
        The PromptBuilder joins sections with '---' separators.
        The first section is the system prompt (MOLE_AI_SYSTEM_PROMPT),
        everything after the first '---' separator is user context/query.
        
        Returns:
            (system_prompt, user_prompt) tuple
        """
        # Split on first occurrence of the section separator
        separator = "\n\n---\n"
        if separator in prompt:
            idx = prompt.index(separator)
            system_prompt = prompt[:idx].strip()
            user_prompt = prompt[idx + len(separator):].strip()
        else:
            # Fallback: use the whole prompt as user content
            system_prompt = "Eres Mole-AI, un agrónomo experto mexicano. Responde en español."
            user_prompt = prompt
        
        return system_prompt, user_prompt

    async def _generate_text_async(self, prompt: str, image_data: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate text in thread pool with robustness and vision support."""
        if not self.model or not self.processor:
            raise RuntimeError("Model not loaded")
        image = None
        final_prompt = prompt
        if image_data:
            try:
                from PIL import Image
                import io
                if image_data.startswith("http"):
                    logger.warning("URL images not supported in local mode yet.")
                else:
                    raw = image_data
                    if "base64," in raw:
                        raw = raw.split("base64,")[1]
                    image_bytes = base64.b64decode(raw)
                    image = Image.open(io.BytesIO(image_bytes))
                    final_prompt = f"<|image_1|>\n{prompt}"
                    logger.info("Image processed for Vision Model")
            except Exception as e:
                logger.error(f"Failed to process image: {e}. Text only.")
                image = None
        formatted_prompt = f"<|user|>\n{final_prompt}<|end|>\n<|assistant|>"
        try:
            if image:
                inputs = await asyncio.to_thread(
                    self.processor, text=formatted_prompt, images=image, return_tensors="pt"
                )
            else:
                inputs = await asyncio.to_thread(
                    self.processor, text=formatted_prompt, return_tensors="pt"
                )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    self.model.generate,
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    use_cache=False,  # FIX: DynamicCache seen_tokens bug
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
            decoded = await asyncio.to_thread(
                self.processor.batch_decode, outputs, skip_special_tokens=True
            )
            response_text = decoded[0]
            clean_text = response_text.replace("<|user|>", "").replace("<|assistant|>", "").replace("<|end|>", "")
            if prompt in clean_text:
                clean_text = clean_text.replace(prompt, "", 1)
            return clean_text.strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

