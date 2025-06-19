import json
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

import redis
from .. import settings

@dataclass
class MarketDataKey:
    """Market data cache key."""
    symbol: str
    source: str
    timestamp: datetime

    def to_string(self) -> str:
        """Convert to cache key string."""
        return f"market_data:{self.symbol}:{self.source}:{self.timestamp.isoformat()}"

@dataclass
class MarketDataConfig:
    """Market data configuration."""
    key: MarketDataKey
    data: Dict[str, Any]
    expiration: int = 3600

class RedisCache:
    """Redis cache implementation."""
    
    def __init__(self) -> None:
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
    def _build_key(self, key_parts: List[str]) -> str:
        """Build Redis key from parts."""
        return ':'.join(['portfolio_analyzer'] + key_parts)
        
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        result = self.redis.get(self._build_key([key]))
        return result if isinstance(result, str) else None
        
    def set(
        self,
        key: str,
        value: str,
        expiration: Optional[int] = None
    ) -> None:
        """Set value in cache with optional expiration in seconds."""
        self.redis.set(
            self._build_key([key]),
            value,
            ex=expiration
        )
        
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
        
    def set_json(
        self,
        key: str,
        value: Any,
        expiration: Optional[int] = None
    ) -> None:
        """Set JSON value in cache."""
        self.set(key, json.dumps(value), expiration)
        
    def get_market_data(
        self,
        symbol: str,
        source: str,
        timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get market data from cache."""
        key = MarketDataKey(symbol, source, timestamp)
        return self.get_json(key.to_string())
        
    def set_market_data(self, config: MarketDataConfig) -> None:
        """Cache market data."""
        self.set_json(config.key.to_string(), config.data, config.expiration)
        
    def get_search_results(
        self,
        query: str,
        source: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get symbol search results from cache."""
        key = f"search:{query}:{source}"
        return self.get_json(key)
        
    def set_search_results(
        self,
        query: str,
        source: str,
        results: List[Dict[str, Any]],
        expiration: int = 3600  # 1 hour
    ) -> None:
        """Cache symbol search results."""
        key = f"search:{query}:{source}"
        self.set_json(key, results, expiration)