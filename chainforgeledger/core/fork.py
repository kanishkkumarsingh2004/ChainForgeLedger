"""
ChainForgeLedger Fork Handling Mechanism

Handles blockchain fork detection and resolution.
"""

import time
from typing import List
from chainforgeledger.core.block import Block
from chainforgeledger.core.blockchain import Blockchain


class ForkHandler:
    """
    Handles blockchain fork detection and resolution.
    
    Attributes:
        blockchain: Reference to the blockchain instance
        fork_threshold: Block height difference to detect a fork
        resolution_strategy: Strategy to use for fork resolution
    """
    
    RESOLUTION_STRATEGIES = ['longest_chain', 'cumulative_difficulty', 'latest_timestamp']
    
    def __init__(self, blockchain: Blockchain, fork_threshold: int = 2, 
                 resolution_strategy: str = 'longest_chain'):
        """
        Initialize a ForkHandler instance.
        
        Args:
            blockchain: Blockchain instance to monitor
            fork_threshold: Block height difference to detect a fork
            resolution_strategy: Fork resolution strategy
        """
        self.blockchain = blockchain
        self.fork_threshold = fork_threshold
        self.resolution_strategy = resolution_strategy
        self.forks = []
        self.last_fork_check = 0
        self.fork_check_interval = 60  # seconds
    
    def detect_fork(self, peer_chain: List[Block]) -> bool:
        """
        Detect if a fork exists between local chain and peer chain.
        
        Args:
            peer_chain: Peer's blockchain to compare
            
        Returns:
            True if a fork is detected
        """
        if len(peer_chain) < 2 or len(self.blockchain.chain) < 2:
            return False
            
        # Find common ancestor
        common_ancestor = None
        min_length = min(len(self.blockchain.chain), len(peer_chain))
        
        for i in range(min_length):
            if self.blockchain.chain[i].hash == peer_chain[i].hash:
                common_ancestor = i
            else:
                break
                
        # Fork detected if common ancestor is found and chain diverges
        if common_ancestor is not None and common_ancestor < min_length - 1:
            # Calculate fork depth
            fork_depth = len(self.blockchain.chain) - common_ancestor - 1
            peer_fork_depth = len(peer_chain) - common_ancestor - 1
            
            # Detect significant forks
            if fork_depth >= self.fork_threshold or peer_fork_depth >= self.fork_threshold:
                fork_info = {
                    'common_ancestor_index': common_ancestor,
                    'common_ancestor_hash': self.blockchain.chain[common_ancestor].hash,
                    'local_fork_length': fork_depth,
                    'peer_fork_length': peer_fork_depth,
                    'detection_time': time.time()
                }
                
                self.forks.append(fork_info)
                return True
                
        return False
    
    def resolve_fork(self, peer_chain: List[Block]) -> bool:
        """
        Resolve a fork between local chain and peer chain.
        
        Args:
            peer_chain: Peer's blockchain to compare
            
        Returns:
            True if fork was resolved successfully
        """
        if not self.detect_fork(peer_chain):
            return False
            
        # Choose resolution strategy
        if self.resolution_strategy == 'longest_chain':
            return self._resolve_by_length(peer_chain)
        elif self.resolution_strategy == 'cumulative_difficulty':
            return self._resolve_by_difficulty(peer_chain)
        elif self.resolution_strategy == 'latest_timestamp':
            return self._resolve_by_timestamp(peer_chain)
        else:
            raise ValueError(f"Unknown resolution strategy: {self.resolution_strategy}")
    
    def _resolve_by_length(self, peer_chain: List[Block]) -> bool:
        """
        Resolve fork by choosing the longest chain.
        
        Args:
            peer_chain: Peer's blockchain to compare
            
        Returns:
            True if local chain was updated
        """
        if len(peer_chain) > len(self.blockchain.chain):
            # Verify peer chain is valid before switching
            if self._is_chain_valid(peer_chain):
                self.blockchain.chain = peer_chain
                self._update_block_hash_map()
                return True
                
        return False
    
    def _resolve_by_difficulty(self, peer_chain: List[Block]) -> bool:
        """
        Resolve fork by choosing chain with highest cumulative difficulty.
        
        Args:
            peer_chain: Peer's blockchain to compare
            
        Returns:
            True if local chain was updated
        """
        local_difficulty = sum(block.difficulty for block in self.blockchain.chain)
        peer_difficulty = sum(block.difficulty for block in peer_chain)
        
        if peer_difficulty > local_difficulty:
            if self._is_chain_valid(peer_chain):
                self.blockchain.chain = peer_chain
                self._update_block_hash_map()
                return True
                
        return False
    
    def _resolve_by_timestamp(self, peer_chain: List[Block]) -> bool:
        """
        Resolve fork by choosing chain with latest block timestamp.
        
        Args:
            peer_chain: Peer's blockchain to compare
            
        Returns:
            True if local chain was updated
        """
        local_timestamp = self.blockchain.get_last_block().timestamp
        peer_timestamp = peer_chain[-1].timestamp
        
        if peer_timestamp > local_timestamp:
            if self._is_chain_valid(peer_chain):
                self.blockchain.chain = peer_chain
                self._update_block_hash_map()
                return True
                
        return False
    
    def _is_chain_valid(self, chain: List[Block]) -> bool:
        """
        Check if a blockchain is valid.
        
        Args:
            chain: Blockchain to validate
            
        Returns:
            True if chain is valid
        """
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            if current_block.index != previous_block.index + 1:
                return False
                
            if current_block.previous_hash != previous_block.hash:
                return False
                
            if not current_block.validate_block():
                return False
                
        return True
    
    def _update_block_hash_map(self):
        """
        Update the block hash map after chain changes.
        """
        self.blockchain._block_hash_map = {}
        for block in self.blockchain.chain:
            self.blockchain._block_hash_map[block.hash] = block
    
    def get_fork_info(self) -> List[dict]:
        """
        Get information about detected forks.
        
        Returns:
            List of fork information dictionaries
        """
        return self.forks
    
    def get_fork_statistics(self) -> dict:
        """
        Get fork statistics.
        
        Returns:
            Fork statistics dictionary
        """
        return {
            'total_forks': len(self.forks),
            'average_fork_depth': sum(f['local_fork_length'] + f['peer_fork_length'] 
                                     for f in self.forks) / len(self.forks) if self.forks else 0,
            'last_fork_time': self.forks[-1]['detection_time'] if self.forks else 0
        }
    
    def clean_up_old_forks(self, max_age: int = 3600):
        """
        Remove old fork information.
        
        Args:
            max_age: Maximum age of fork information to keep in seconds
        """
        current_time = time.time()
        self.forks = [f for f in self.forks if current_time - f['detection_time'] <= max_age]
    
    def set_resolution_strategy(self, strategy: str):
        """
        Set the fork resolution strategy.
        
        Args:
            strategy: Resolution strategy to use
            
        Raises:
            ValueError: If strategy is not recognized
        """
        if strategy not in self.RESOLUTION_STRATEGIES:
            raise ValueError(f"Unsupported resolution strategy: {strategy}")
            
        self.resolution_strategy = strategy
    
    def set_fork_threshold(self, threshold: int):
        """
        Set the fork detection threshold.
        
        Args:
            threshold: Block height difference threshold
        """
        if threshold < 1:
            raise ValueError("Fork threshold must be at least 1")
            
        self.fork_threshold = threshold
    
    def __repr__(self):
        """String representation of the ForkHandler."""
        stats = self.get_fork_statistics()
        return (f"ForkHandler(strategy={self.resolution_strategy}, "
                f"threshold={self.fork_threshold}, "
                f"forks={stats['total_forks']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_fork_statistics()
        return (
            f"Fork Handler\n"
            f"=============\n"
            f"Resolution Strategy: {self.resolution_strategy}\n"
            f"Fork Threshold: {self.fork_threshold} blocks\n"
            f"Total Forks Detected: {stats['total_forks']}\n"
            f"Average Fork Depth: {stats['average_fork_depth']:.1f} blocks\n"
            f"Last Fork Time: {time.ctime(stats['last_fork_time'])}"
        )
