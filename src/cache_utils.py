from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class ResponseCache:
    """Shared response cache with TTL for all scrapers"""
    def __init__(self, ttl_hours: int = 1):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, url: str) -> Optional[Tuple[datetime, Any]]:
        """Get cached response if exists and not expired"""
        if url in self.cache:
            cached_time, content = self.cache[url]
            if datetime.now(timezone.utc) - cached_time < self.ttl:
                return content
            del self.cache[url]  # Remove expired entry
        return None
    
    def set(self, url: str, content: Any) -> None:
        """Cache a response with current timestamp"""
        self.cache[url] = (datetime.now(timezone.utc), content)
    
    def clear(self) -> None:
        """Clear all cached responses"""
        self.cache.clear()

# Shared cache instance
shared_cache = ResponseCache()
