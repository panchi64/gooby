import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
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
    
    async def chat_completion(self, messages: List[Dict[str, str]], system_prompt: str = None) -> Optional[str]:
        """
        Send a chat completion request to LM Studio
        
        Args:
            messages: List of message objects with 'role' and 'content'
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
            
            chat_messages.extend(messages)
            
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
    "Oops! My goobly brain is taking a nap right now! 😴",
    "Hmm, seems like my goob circuits are a bit fuzzy! Try again in a sec! 🤖",
    "Uh oh, my LLM buddy is being shy right now! Give me a moment! 🫘",
    "Looks like I'm having a goobly moment! Be right back! ⏰",
    "My thinking cap is in the wash! One sec, goober! 🧢"
]

async def get_fallback_response() -> str:
    """Get a random fallback response when LM Studio is down"""
    import random
    return random.choice(FALLBACK_RESPONSES)