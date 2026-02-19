"""
ChainForgeLedger Node Rate Limiting

Implements rate limiting for node operations to prevent abuse.
"""

import time
from typing import Dict, List
from collections import defaultdict


class RateLimiter:
    """
    Implements rate limiting for node operations.
    
    Attributes:
        limits: Rate limits per operation type
        requests: Track of requests per client
        cooldown_period: Cooldown period for temporary bans
    """
    
    DEFAULT_LIMITS = {
        'transaction': 100,  # transactions per minute
        'block': 10,         # blocks per minute
        'peer_request': 50,  # peer requests per minute
        'api_request': 200,  # API requests per minute
        'connection': 10     # new connections per minute
    }
    
    TIME_WINDOWS = {
        'minute': 60,
        'hour': 3600,
        'day': 86400
    }
    
    def __init__(self, limits: Dict = None, cooldown_period: int = 3600):
        """
        Initialize a RateLimiter instance.
        
        Args:
            limits: Optional custom rate limits
            cooldown_period: Cooldown period for temporary bans in seconds
        """
        self.limits = limits or self.DEFAULT_LIMITS.copy()
        self.requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.banned_clients: Dict[str, float] = {}
        self.cooldown_period = cooldown_period
        self.last_cleanup = time.time()
    
    def is_rate_limited(self, client_id: str, operation: str, 
                      time_window: str = 'minute') -> bool:
        """
        Check if a client is rate limited for a specific operation.
        
        Args:
            client_id: Client identifier (IP address, node ID, etc.)
            operation: Operation type to check
            time_window: Time window for rate limiting
            
        Returns:
            True if client is rate limited
        """
        # Check if client is banned
        if self.is_banned(client_id):
            return True
            
        # Check if operation is valid
        if operation not in self.limits:
            return False
            
        # Get current time and time window duration
        current_time = time.time()
        window_duration = self.TIME_WINDOWS.get(time_window, 60)
        
        # Get requests for this client and operation
        client_requests = self.requests[client_id][operation]
        
        # Remove old requests
        client_requests = [t for t in client_requests if current_time - t < window_duration]
        self.requests[client_id][operation] = client_requests
        
        # Check rate limit
        limit = self.limits[operation]
        return len(client_requests) >= limit
    
    def record_request(self, client_id: str, operation: str) -> bool:
        """
        Record a request and check if it's rate limited.
        
        Args:
            client_id: Client identifier
            operation: Operation type
            
        Returns:
            True if request was recorded successfully (not rate limited)
        """
        if self.is_rate_limited(client_id, operation):
            self.ban_client(client_id)
            return False
            
        current_time = time.time()
        self.requests[client_id][operation].append(current_time)
        return True
    
    def ban_client(self, client_id: str, ban_duration: int = None):
        """
        Ban a client temporarily.
        
        Args:
            client_id: Client identifier
            ban_duration: Ban duration in seconds (default: cooldown_period)
        """
        ban_duration = ban_duration or self.cooldown_period
        self.banned_clients[client_id] = time.time() + ban_duration
    
    def unban_client(self, client_id: str):
        """
        Unban a client.
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.banned_clients:
            del self.banned_clients[client_id]
    
    def is_banned(self, client_id: str) -> bool:
        """
        Check if a client is banned.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if client is banned
        """
        if client_id not in self.banned_clients:
            return False
            
        if time.time() > self.banned_clients[client_id]:
            del self.banned_clients[client_id]
            return False
            
        return True
    
    def get_ban_time_remaining(self, client_id: str) -> float:
        """
        Get remaining ban time for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Remaining ban time in seconds
        """
        if not self.is_banned(client_id):
            return 0
            
        remaining = self.banned_clients[client_id] - time.time()
        return max(0, remaining)
    
    def set_rate_limit(self, operation: str, limit: int):
        """
        Set rate limit for an operation.
        
        Args:
            operation: Operation type
            limit: Maximum number of requests per time window
            
        Raises:
            ValueError: If limit is invalid
        """
        if limit < 0:
            raise ValueError("Rate limit must be non-negative")
            
        self.limits[operation] = limit
    
    def get_rate_limit(self, operation: str) -> int:
        """
        Get rate limit for an operation.
        
        Args:
            operation: Operation type
            
        Returns:
            Rate limit for the operation
        """
        return self.limits.get(operation, 0)
    
    def get_request_count(self, client_id: str, operation: str, 
                        time_window: str = 'minute') -> int:
        """
        Get request count for a client and operation.
        
        Args:
            client_id: Client identifier
            operation: Operation type
            time_window: Time window
            
        Returns:
            Number of requests in the time window
        """
        if client_id not in self.requests or operation not in self.requests[client_id]:
            return 0
            
        current_time = time.time()
        window_duration = self.TIME_WINDOWS.get(time_window, 60)
        
        return len([t for t in self.requests[client_id][operation] 
                  if current_time - t < window_duration])
    
    def get_remaining_limit(self, client_id: str, operation: str, 
                          time_window: str = 'minute') -> int:
        """
        Get remaining rate limit for a client and operation.
        
        Args:
            client_id: Client identifier
            operation: Operation type
            time_window: Time window
            
        Returns:
            Remaining requests allowed
        """
        limit = self.get_rate_limit(operation)
        count = self.get_request_count(client_id, operation, time_window)
        return max(0, limit - count)
    
    def cleanup_old_requests(self):
        """Clean up old requests to save memory."""
        current_time = time.time()
        
        # Cleanup if last cleanup was more than 5 minutes ago
        if current_time - self.last_cleanup < 300:
            return
            
        self.last_cleanup = current_time
        
        for client_id in list(self.requests.keys()):
            for operation in list(self.requests[client_id].keys()):
                # Remove requests older than 1 day
                self.requests[client_id][operation] = [
                    t for t in self.requests[client_id][operation] 
                    if current_time - t < self.TIME_WINDOWS['day']
                ]
                
                # Remove operation entry if no requests
                if not self.requests[client_id][operation]:
                    del self.requests[client_id][operation]
            
            # Remove client entry if no operations
            if not self.requests[client_id]:
                del self.requests[client_id]
    
    def get_statistics(self) -> Dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Statistics dictionary
        """
        # Cleanup old requests first
        self.cleanup_old_requests()
        
        total_clients = len(self.requests)
        total_banned = len(self.banned_clients)
        total_requests = sum(
            len(ops.values()) for ops in self.requests.values()
        )
        
        operation_stats = {}
        for operation in self.limits:
            operation_count = sum(
                len(times) for client in self.requests.values() 
                for op, times in client.items() if op == operation
            )
            operation_stats[operation] = operation_count
        
        return {
            'total_clients': total_clients,
            'total_banned': total_banned,
            'total_requests': total_requests,
            'operation_stats': operation_stats
        }
    
    def get_client_stats(self, client_id: str) -> Dict:
        """
        Get statistics for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client statistics dictionary
        """
        if client_id not in self.requests and client_id not in self.banned_clients:
            return {}
            
        client_stats = {
            'client_id': client_id,
            'is_banned': self.is_banned(client_id),
            'ban_time_remaining': self.get_ban_time_remaining(client_id),
            'operations': {}
        }
        
        if client_id in self.requests:
            for operation in self.requests[client_id]:
                client_stats['operations'][operation] = {
                    'requests': len(self.requests[client_id][operation]),
                    'limit': self.limits.get(operation, 0),
                    'remaining': self.get_remaining_limit(client_id, operation)
                }
        
        return client_stats
    
    def reset_client_stats(self, client_id: str):
        """
        Reset statistics for a client.
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.requests:
            del self.requests[client_id]
            
        if client_id in self.banned_clients:
            del self.banned_clients[client_id]
    
    def reset_all_stats(self):
        """Reset all rate limiter statistics."""
        self.requests.clear()
        self.banned_clients.clear()
        self.last_cleanup = time.time()
    
    def __repr__(self):
        """String representation of the RateLimiter."""
        stats = self.get_statistics()
        return (f"RateLimiter(clients={stats['total_clients']}, "
                f"banned={stats['total_banned']}, "
                f"requests={stats['total_requests']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_statistics()
        return (
            f"Rate Limiter\n"
            f"=============\n"
            f"Total Clients: {stats['total_clients']}\n"
            f"Banned Clients: {stats['total_banned']}\n"
            f"Total Requests: {stats['total_requests']}\n"
            f"Operations:\n"
            f"{chr(10).join([f'  {op}: {count}' for op, count in stats['operation_stats'].items()])}"
        )
