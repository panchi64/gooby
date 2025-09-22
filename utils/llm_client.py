import aiohttp
import asyncio
import logging
import base64
from typing import List, Dict, Optional, Union
from config import Config

logger = logging.getLogger(__name__)

class LMStudioClient:
    def __init__(self):
        self.base_url = Config.LM_STUDIO_URL
        self.timeout = Config.LM_STUDIO_TIMEOUT
        self.session = None
        self.models_url = Config.LM_STUDIO_URL.replace('/v1/chat/completions', '/v1/models')
        self._cached_model = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def encode_image_to_base64(self, image_data: bytes) -> str:
        """
        Encode image bytes to base64 string for LM Studio API
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    async def get_loaded_model(self) -> Optional[str]:
        """
        Get the currently loaded model from LM Studio

        Returns:
            Model identifier string or None if failed
        """
        if self._cached_model:
            return self._cached_model

        try:
            async with self.session.get(self.models_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Find the first loaded model
                    for model in data.get('data', []):
                        if model.get('loaded', False):
                            self._cached_model = model.get('id')
                            logger.debug(f"Detected loaded model: {self._cached_model}")
                            return self._cached_model

                    # If no loaded models found, try to get any available model
                    if data.get('data'):
                        self._cached_model = data['data'][0].get('id')
                        logger.debug(f"Using first available model: {self._cached_model}")
                        return self._cached_model

                else:
                    logger.warning(f"Failed to get models from LM Studio: {response.status}")

        except Exception as e:
            logger.warning(f"Error getting loaded model from LM Studio: {e}")

        return None

    async def download_discord_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from Discord CDN
        
        Args:
            image_url: Discord CDN URL
            
        Returns:
            Image bytes or None if download failed
        """
        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Failed to download image: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error downloading Discord image: {e}")
            return None
    
    async def chat_completion(self, messages: List[Dict[str, Union[str, List]]], system_prompt: str = None) -> Optional[str]:
        """
        Send a chat completion request to LM Studio (supports text and images)
        
        Args:
            messages: List of message objects with 'role' and 'content'
                     Content can be string (text) or list (multimodal)
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Response content or None if failed
        """
        try:
            # Prepare messages
            chat_messages = []
            
            if system_prompt:
                chat_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Process messages to handle both text and multimodal content
            for msg in messages:
                processed_msg = {
                    "role": msg["role"]
                }
                
                # Handle multimodal content (list) vs simple text (string)
                if isinstance(msg["content"], list):
                    # Multimodal message with text and/or images
                    processed_msg["content"] = msg["content"]
                else:
                    # Simple text message
                    processed_msg["content"] = msg["content"]
                
                chat_messages.append(processed_msg)
            
            # Get the loaded model dynamically
            loaded_model = await self.get_loaded_model()

            # Prepare request payload
            payload = {
                "messages": chat_messages,
                "stream": False
            }

            # Add model if we can detect it, otherwise let LM Studio use the loaded one
            if loaded_model:
                payload["model"] = loaded_model
                logger.debug(f"Using detected model: {loaded_model}")
            else:
                # Fallback to generic name - LM Studio will ignore it anyway with single model
                payload["model"] = "gpt-3.5-turbo"
                logger.debug("Using fallback model name (LM Studio will use loaded model)")

            # Add max_tokens only if configured and reasonable
            if Config.MAX_TOKENS > 0:
                payload["max_tokens"] = Config.MAX_TOKENS
                logger.debug(f"Setting max_tokens to: {Config.MAX_TOKENS}")
            else:
                logger.debug("Using LM Studio default max_tokens")

            # Note: Removed temperature to let LM Studio use its configured value
            logger.debug(f"Sending LM Studio request: {len(chat_messages)} messages, payload keys: {list(payload.keys())}")
            
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()

                    # Debug: Log the full response structure
                    logger.debug(f"Full LM Studio response keys: {list(data.keys())}")
                    choices = data.get('choices', [])
                    logger.debug(f"Choices count: {len(choices)}")

                    if choices:
                        choice = choices[0]
                        logger.debug(f"First choice keys: {list(choice.keys())}")
                        message = choice.get('message', {})
                        logger.debug(f"Message keys: {list(message.keys())}")
                        content = message.get('content', '')

                        # Check for native reasoning content
                        reasoning_content = message.get('reasoning_content', '')
                        if reasoning_content:
                            logger.debug(f"Reasoning content found: {len(reasoning_content)} chars")
                            logger.debug(f"Reasoning preview: {repr(reasoning_content[:100])}")

                        logger.debug(f"Raw content type: {type(content)}, length: {len(content) if content else 'None'}")
                        if content:
                            logger.debug(f"Content preview: {repr(content[:100])}")
                    else:
                        content = ''
                        logger.warning("No choices in response!")

                    # Check finish reason for debugging token limits
                    finish_reason = data.get('choices', [{}])[0].get('finish_reason', 'unknown')
                    usage = data.get('usage', {})
                    completion_tokens = usage.get('completion_tokens', 'unknown')

                    logger.debug(f"LM Studio response: {len(content)} chars, finish_reason: {finish_reason}, completion_tokens: {completion_tokens}")

                    if finish_reason == 'length':
                        logger.warning(f"Response truncated due to length limit! Used {completion_tokens} tokens, requested max: {Config.MAX_TOKENS}")

                    return content.strip() if content else None
                else:
                    error_text = await response.text()
                    logger.error(f"LM Studio error {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("LM Studio request timed out")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"LM Studio connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected LM Studio error: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """
        Test connection to LM Studio
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            response = await self.chat_completion(test_messages)
            return response is not None
        except Exception as e:
            logger.error(f"LM Studio connection test failed: {e}")
            return False

# Fallback responses when LM Studio is unavailable
FALLBACK_RESPONSES = [
    "Well this is awkward. My brain decided to take a vacation.",
    "LLM's having a moment. Fantastic timing as usual.",
    "Yeah, so that didn't work. Try again if you feel like it.",
    "My thinking apparatus is temporarily out of order.",
    "Connection issues. Because of course there are."
]

async def get_fallback_response() -> str:
    """Get a random fallback response when LM Studio is down"""
    import random
    return random.choice(FALLBACK_RESPONSES)