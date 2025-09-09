import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class ImageSearcher:
    def __init__(self):
        self.session = None
        self.max_results = 10
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for images using DuckDuckGo (free, no API key required)
        
        Args:
            query: Search term
            max_results: Maximum number of results to return
            
        Returns:
            List of image result dictionaries
        """
        try:
            results = []
            
            # Run synchronous DDGS in executor to avoid blocking
            def sync_search():
                with DDGS() as ddg:
                    return list(ddg.images(
                        keywords=query,
                        region='us-en',
                        safesearch='moderate',
                        size=None,
                        color=None,
                        type_image=None,
                        layout=None,
                        license_image=None,
                        max_results=max_results * 2  # Get more to filter
                    ))
            
            loop = asyncio.get_event_loop()
            ddg_results = await loop.run_in_executor(None, sync_search)
            
            for i, result in enumerate(ddg_results):
                if i >= max_results:
                    break
                    
                # Filter out potentially problematic images
                image_url = result.get('image', '')
                title = result.get('title', 'Untitled')
                source = result.get('source', 'Unknown')
                
                # Basic URL validation
                if not image_url or not image_url.startswith(('http://', 'https://')):
                    continue
                    
                # Skip very long URLs (often dynamic/temporary)
                if len(image_url) > 500:
                    continue
                
                results.append({
                    'title': title[:100],  # Truncate long titles
                    'url': image_url,
                    'source': source[:50],  # Truncate long source names
                    'thumbnail': result.get('thumbnail', image_url)
                })
        
            logger.info(f"Found {len(results)} images for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def search_images(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for images using multiple sources
        
        Args:
            query: Search term
            max_results: Maximum number of results
            
        Returns:
            List of image results
        """
        # Clean up the query
        clean_query = query.strip()[:100]  # Limit query length
        
        if not clean_query:
            return []
        
        # Add some safety terms for better results
        safe_query = f"{clean_query} -nsfw -explicit"
        
        # Try DuckDuckGo first
        results = await self.search_duckduckgo(safe_query, max_results)
        
        # If no results, try without safety terms
        if not results:
            logger.info(f"No results with safe query, trying original: {clean_query}")
            results = await self.search_duckduckgo(clean_query, max_results)
        
        return results
    
    async def verify_image_url(self, url: str) -> bool:
        """
        Verify that an image URL is accessible
        
        Args:
            url: Image URL to verify
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            if not self.session:
                return False
                
            async with self.session.head(url, timeout=5) as response:
                # Check if it's an image
                content_type = response.headers.get('content-type', '').lower()
                
                return (response.status == 200 and 
                       any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']))
                       
        except Exception as e:
            logger.debug(f"URL verification failed for {url}: {e}")
            return False
    
    def is_safe_query(self, query: str) -> bool:
        """
        Basic check if query is safe for searching
        
        Args:
            query: Search query
            
        Returns:
            True if query appears safe
        """
        # List of terms to avoid
        unsafe_terms = [
            'porn', 'nude', 'naked', 'sex', 'explicit', 'nsfw',
            'gore', 'violence', 'drugs', 'illegal'
        ]
        
        query_lower = query.lower()
        
        for term in unsafe_terms:
            if term in query_lower:
                return False
        
        return True
    
    async def search_with_fallback(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search with fallback options if initial search fails
        
        Args:
            query: Search term
            max_results: Maximum results
            
        Returns:
            List of image results
        """
        # Check if query is safe
        if not self.is_safe_query(query):
            logger.warning(f"Potentially unsafe query blocked: {query}")
            return []
        
        # Try main search
        results = await self.search_images(query, max_results)
        
        # If no results, try variations
        if not results and len(query.split()) > 1:
            # Try with fewer words
            shorter_query = " ".join(query.split()[:3])
            logger.info(f"Trying shorter query: {shorter_query}")
            results = await self.search_images(shorter_query, max_results)
        
        # Verify URLs (optional, can be slow)
        # verified_results = []
        # for result in results[:3]:  # Only verify first 3
        #     if await self.verify_image_url(result['url']):
        #         verified_results.append(result)
        # 
        # return verified_results if verified_results else results
        
        return results