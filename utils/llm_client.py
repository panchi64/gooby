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
            
            # Prepare request payload
            payload = {
                "model": "gpt-3.5-turbo",  # LM Studio ignores this but requires it
                "messages": chat_messages,
                "temperature": Config.TEMPERATURE,
                "max_tokens": Config.MAX_TOKENS,
                "stream": False
            }
            
            logger.debug(f"Sending LM Studio request: {len(chat_messages)} messages")
            
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.debug(f"LM Studio response received: {len(content)} characters")
                    return content.strip()
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