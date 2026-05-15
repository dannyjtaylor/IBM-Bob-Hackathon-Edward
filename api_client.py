"""
Edward API Client
Handles communication with IBM Bob API
"""

import httpx
from typing import Optional, AsyncIterator
import base64

from config import IBM_BOB_API_URL, IBM_BOB_API_KEY
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class BobAPIClient:
    """
    Client for communicating with IBM Bob API.
    Handles screenshot + question submission and streaming responses.
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            api_url: IBM Bob API URL (defaults to config)
            api_key: IBM Bob API key (defaults to config)
        """
        self.api_url = api_url or IBM_BOB_API_URL
        self.api_key = api_key or IBM_BOB_API_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"Bob API Client initialized: {self.api_url}")
    
    async def ask_question(
        self,
        question: str,
        screenshot_base64: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Send question to Bob API with optional screenshot.
        
        Args:
            question: User's question
            screenshot_base64: Base64-encoded screenshot (optional)
            stream: If True, stream response chunks
            
        Yields:
            Response text chunks (if streaming)
            
        Returns:
            Complete response (if not streaming)
        """
        try:
            # Prepare request payload
            payload = {
                "question": question,
                "screenshot": screenshot_base64,
                "stream": stream
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Sending question to Bob API: {question[:50]}...")
            
            if stream:
                # Stream response
                async with self.client.stream(
                    "POST",
                    f"{self.api_url}/ask",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
            else:
                # Get complete response
                response = await self.client.post(
                    f"{self.api_url}/ask",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                yield result.get("response", "")
                
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            yield f"Error: Failed to communicate with Bob API - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"Error: {str(e)}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("API client closed")


# Singleton instance
_api_client: Optional[BobAPIClient] = None


def get_api_client() -> BobAPIClient:
    """
    Get or create singleton API client instance.
    
    Returns:
        BobAPIClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = BobAPIClient()
    return _api_client

# Made with Bob
