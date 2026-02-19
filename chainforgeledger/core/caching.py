"""
ChainForgeLedger Caching Layer

Implements caching mechanisms for blockchain performance optimization.
"""

import time
from typing import Dict, List, Optional, Any
from collections import OrderedDict


class BlockchainCache:
    """
    Caching layer for blockchain operations.
    
    Attributes:
        caches: Dictionary of cache instances by cache type
        cache_configs: Configuration for each cache type
        hit_counts: Cache hit statistics
        miss_counts: Cache miss statistics
        eviction_counts: Cache eviction statistics
    """
    
    CACHE_TYPES = ['blocks', 'transactions', 'accounts', 'contracts', 'metadata']
    
    DEFAULT_CACHE_CONFIG = {
        'blocks': {'max_size': 1000, 'ttl': 3600},
        'transactions': {'max_size': 5000, 'ttl': 1800},
        'accounts': {'max_size': 10000, 'ttl': 900},
        'contracts': {'max_size': 500, 'ttl': 7200},
        'metadata': {'max_size': 500, 'ttl': 86400}
    }
    
    def __init__(self, cache_configs: Dict = None):
        """
        Initialize a BlockchainCache instance.
        
        Args:
            cache_configs: Optional custom cache configurations
        """
        self.caches: Dict[str, OrderedDict] = {}
        self.cache_configs = cache_configs or self.DEFAULT_CACHE_CONFIG.copy()
        self.hit_counts: Dict[str, int] = {cache_type: 0 for cache_type in self.CACHE_TYPES}
        self.miss_counts: Dict[str, int] = {cache_type: 0 for cache_type in self.CACHE_TYPES}
        self.eviction_counts: Dict[str, int] = {cache_type: 0 for cache_type in self.CACHE_TYPES}
        self._initialize_caches()
    
    def _initialize_caches(self):
        """Initialize cache instances."""
        for cache_type in self.CACHE_TYPES:
            self.caches[cache_type] = OrderedDict()
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            cache_type: Cache type (blocks/transactions/accounts/contracts/metadata)
            key: Cache key
            
        Returns:
            Cached item if found and not expired, None otherwise
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        cache = self.caches[cache_type]
        
        if key in cache:
            item, timestamp = cache[key]
            
            # Check TTL
            config = self.cache_configs.get(cache_type, {})
            ttl = config.get('ttl', 3600)
            
            if time.time() - timestamp <= ttl:
                # Move to front (LRU behavior)
                del cache[key]
                cache[key] = (item, timestamp)
                self.hit_counts[cache_type] += 1
                return item
            else:
                # Remove expired item
                del cache[key]
        
        self.miss_counts[cache_type] += 1
        return None
    
    def set(self, cache_type: str, key: str, value: Any) -> None:
        """
        Set item in cache.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Value to cache
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        cache = self.caches[cache_type]
        config = self.cache_configs.get(cache_type, {})
        max_size = config.get('max_size', 1000)
        
        # Remove existing entry if present
        if key in cache:
            del cache[key]
        
        # Evict LRU item if cache is full
        if len(cache) >= max_size:
            cache.popitem(last=False)  # Remove first item (LRU)
            self.eviction_counts[cache_type] += 1
        
        # Add new item
        cache[key] = (value, time.time())
    
    def delete(self, cache_type: str, key: str) -> bool:
        """
        Delete item from cache.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            True if item was deleted, False if not found
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        cache = self.caches[cache_type]
        
        if key in cache:
            del cache[key]
            return True
            
        return False
    
    def clear_cache(self, cache_type: str = None):
        """
        Clear cache.
        
        Args:
            cache_type: Optional cache type to clear (if None, clears all caches)
        """
        if cache_type:
            if cache_type not in self.CACHE_TYPES:
                raise ValueError(f"Invalid cache type: {cache_type}")
                
            self.caches[cache_type].clear()
            self.hit_counts[cache_type] = 0
            self.miss_counts[cache_type] = 0
            self.eviction_counts[cache_type] = 0
        else:
            for cache_type in self.CACHE_TYPES:
                self.caches[cache_type].clear()
                self.hit_counts[cache_type] = 0
                self.miss_counts[cache_type] = 0
                self.eviction_counts[cache_type] = 0
    
    def get_cache_stats(self, cache_type: str = None) -> Dict:
        """
        Get cache statistics.
        
        Args:
            cache_type: Optional cache type to get stats for
            
        Returns:
            Cache statistics dictionary
        """
        if cache_type:
            if cache_type not in self.CACHE_TYPES:
                raise ValueError(f"Invalid cache type: {cache_type}")
                
            total_requests = self.hit_counts[cache_type] + self.miss_counts[cache_type]
            hit_rate = (self.hit_counts[cache_type] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_type': cache_type,
                'size': len(self.caches[cache_type]),
                'max_size': self.cache_configs.get(cache_type, {}).get('max_size', 0),
                'hits': self.hit_counts[cache_type],
                'misses': self.miss_counts[cache_type],
                'evictions': self.eviction_counts[cache_type],
                'total_requests': total_requests,
                'hit_rate': hit_rate
            }
        else:
            all_stats = []
            for cache_type in self.CACHE_TYPES:
                stats = self.get_cache_stats(cache_type)
                all_stats.append(stats)
                
            # Calculate overall statistics
            total_hits = sum(stats['hits'] for stats in all_stats)
            total_misses = sum(stats['misses'] for stats in all_stats)
            total_requests = total_hits + total_misses
            overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            total_evictions = sum(stats['evictions'] for stats in all_stats)
            total_size = sum(stats['size'] for stats in all_stats)
            total_max_size = sum(stats['max_size'] for stats in all_stats)
            
            return {
                'overall': {
                    'hits': total_hits,
                    'misses': total_misses,
                    'evictions': total_evictions,
                    'total_requests': total_requests,
                    'hit_rate': overall_hit_rate,
                    'size': total_size,
                    'max_size': total_max_size
                },
                'per_cache': all_stats
            }
    
    def set_cache_config(self, cache_type: str, config: Dict):
        """
        Set cache configuration.
        
        Args:
            cache_type: Cache type
            config: Configuration dictionary with 'max_size' and 'ttl' keys
            
        Raises:
            ValueError: If cache type is invalid or configuration is invalid
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        if 'max_size' in config:
            if not isinstance(config['max_size'], int) or config['max_size'] <= 0:
                raise ValueError("max_size must be a positive integer")
                
        if 'ttl' in config:
            if not isinstance(config['ttl'], int) or config['ttl'] <= 0:
                raise ValueError("ttl must be a positive integer")
                
        self.cache_configs[cache_type] = config
        
        # If max_size is reduced, evict old items
        if 'max_size' in config:
            max_size = config['max_size']
            cache = self.caches[cache_type]
            
            while len(cache) > max_size:
                cache.popitem(last=False)
                self.eviction_counts[cache_type] += 1
    
    def get_cache_config(self, cache_type: str) -> Dict:
        """
        Get cache configuration.
        
        Args:
            cache_type: Cache type
            
        Returns:
            Cache configuration dictionary
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        return self.cache_configs.get(cache_type, {})
    
    def purge_expired_items(self, cache_type: str = None) -> int:
        """
        Purge expired items from cache.
        
        Args:
            cache_type: Optional cache type to purge
            
        Returns:
            Number of expired items removed
        """
        removed = 0
        
        if cache_type:
            if cache_type not in self.CACHE_TYPES:
                raise ValueError(f"Invalid cache type: {cache_type}")
                
            removed = self._purge_cache(cache_type)
        else:
            for cache_type in self.CACHE_TYPES:
                removed += self._purge_cache(cache_type)
                
        return removed
    
    def _purge_cache(self, cache_type: str) -> int:
        """Purge expired items from a specific cache."""
        cache = self.caches[cache_type]
        config = self.cache_configs.get(cache_type, {})
        ttl = config.get('ttl', 3600)
        removed = 0
        
        keys_to_remove = []
        
        for key, (item, timestamp) in cache.items():
            if time.time() - timestamp > ttl:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del cache[key]
            removed += 1
            
        return removed
    
    def get_active_items(self, cache_type: str) -> List[Dict]:
        """
        Get active items in cache with metadata.
        
        Args:
            cache_type: Cache type
            
        Returns:
            List of active items with metadata
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        cache = self.caches[cache_type]
        config = self.cache_configs.get(cache_type, {})
        ttl = config.get('ttl', 3600)
        
        items = []
        
        for key, (item, timestamp) in cache.items():
            time_remaining = max(0, ttl - (time.time() - timestamp))
            
            items.append({
                'key': key,
                'value': item,
                'timestamp': timestamp,
                'time_remaining': time_remaining,
                'time_remaining_percent': (time_remaining / ttl) * 100 if ttl > 0 else 0
            })
            
        # Sort by time remaining
        return sorted(items, key=lambda x: x['time_remaining'])
    
    def warmup_cache(self, cache_type: str, keys: List[str], 
                    loader_func: callable) -> int:
        """
        Warm up cache by loading items.
        
        Args:
            cache_type: Cache type
            keys: List of keys to preload
            loader_func: Function to load item given key
            
        Returns:
            Number of items successfully loaded into cache
        """
        if cache_type not in self.CACHE_TYPES:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
        loaded = 0
        
        for key in keys:
            if key not in self.caches[cache_type]:
                try:
                    value = loader_func(key)
                    self.set(cache_type, key, value)
                    loaded += 1
                except Exception as e:
                    print(f"Failed to load cache item {key}: {e}")
                    
        return loaded
    
    def __repr__(self):
        """String representation of the BlockchainCache."""
        stats = self.get_cache_stats()
        overall = stats['overall']
        return (f"BlockchainCache(hits={overall['hits']}, "
                f"misses={overall['misses']}, "
                f"hit_rate={overall['hit_rate']:.1f}%)")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_cache_stats()
        overall = stats['overall']
        
        per_cache_str = []
        for cache_type in self.CACHE_TYPES:
            cache_stats = next(stats['per_cache'] for stats['per_cache'] in 
                            stats['per_cache'] if stats['per_cache']['cache_type'] == cache_type)
            per_cache_str.append(
                f"{cache_type}: {cache_stats['size']}/{cache_stats['max_size']} "
                f"({cache_stats['hit_rate']:.1f}% hit rate)"
            )
        
        return (
            f"Blockchain Cache\n"
            f"================\n"
            f"Overall Stats:\n"
            f"  Hits: {overall['hits']:,}\n"
            f"  Misses: {overall['misses']:,}\n"
            f"  Evictions: {overall['evictions']:,}\n"
            f"  Hit Rate: {overall['hit_rate']:.1f}%\n"
            f"  Total Size: {overall['size']}/{overall['max_size']}\n"
            f"\nPer-Cache Stats:\n"
            f"{chr(10).join(f'  {s}' for s in per_cache_str)}"
        )
