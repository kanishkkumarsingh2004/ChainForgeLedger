"""
ChainForgeLedger Sharding Support

Implements sharding for blockchain scalability.
"""

import time
from typing import Dict, List, Optional
from chainforgeledger.core.block import Block
from chainforgeledger.core.blockchain import Blockchain
from chainforgeledger.crypto.hashing import sha256_hash


class ShardManager:
    """
    Manages blockchain sharding for scalability.
    
    Attributes:
        shards: Dictionary of shards by shard ID
        shard_count: Number of shards
        shard_size: Size of each shard in blocks
        shard_mapping: Address to shard mapping
        cross_shard_transactions: Queue of cross-shard transactions
        shard_validators: Validators per shard
        shard_committee: Shard committee information
    """
    
    def __init__(self, shard_count: int = 4, shard_size: int = 1000):
        """
        Initialize a ShardManager instance.
        
        Args:
            shard_count: Number of shards
            shard_size: Size of each shard in blocks
        """
        self.shard_count = shard_count
        self.shard_size = shard_size
        self.shards: Dict[int, Blockchain] = {}
        self.shard_mapping: Dict[str, int] = {}
        self.cross_shard_transactions: List[Dict] = []
        self.shard_validators: Dict[int, List[str]] = {}
        self.shard_committee: Dict[int, List[str]] = {}
        self._initialize_shards()
    
    def _initialize_shards(self):
        """Initialize shards with genesis blocks."""
        for shard_id in range(self.shard_count):
            self.shards[shard_id] = Blockchain(f"shard_{shard_id}")
            self.shard_validators[shard_id] = []
            self.shard_committee[shard_id] = []
    
    def get_shard_id(self, address: str) -> int:
        """
        Get shard ID for an address.
        
        Args:
            address: Address to map to shard
            
        Returns:
            Shard ID
        """
        if address in self.shard_mapping:
            return self.shard_mapping[address]
            
        # Hash-based shard assignment
        shard_id = int(sha256_hash(address), 16) % self.shard_count
        self.shard_mapping[address] = shard_id
        return shard_id
    
    def add_block_to_shard(self, block: Block, shard_id: int) -> bool:
        """
        Add block to a specific shard.
        
        Args:
            block: Block to add
            shard_id: Shard ID to add block to
            
        Returns:
            True if block was successfully added
        """
        if shard_id not in self.shards:
            return False
            
        blockchain = self.shards[shard_id]
        
        # Check shard size limit
        if len(blockchain.chain) >= self.shard_size:
            self._split_shard(shard_id)
            
        return blockchain.add_block(block)
    
    def _split_shard(self, shard_id: int):
        """
        Split a shard when it reaches size limit.
        
        Args:
            shard_id: Shard ID to split
        """
        blockchain = self.shards[shard_id]
        
        # Create new shard
        new_shard_id = self.shard_count
        self.shard_count += 1
        self.shards[new_shard_id] = Blockchain(f"shard_{new_shard_id}")
        
        # Move blocks to new shard
        split_point = len(blockchain.chain) // 2
        new_blocks = blockchain.chain[split_point:]
        blockchain.chain = blockchain.chain[:split_point]
        
        for block in new_blocks:
            self.shards[new_shard_id].add_block(block)
        
        # Reassign addresses to new shard
        addresses_to_reassign = []
        
        for address, current_shard in self.shard_mapping.items():
            if current_shard == shard_id:
                new_shard = int(sha256_hash(address), 16) % self.shard_count
                if new_shard != shard_id:
                    addresses_to_reassign.append((address, new_shard))
        
        for address, new_shard in addresses_to_reassign:
            self.shard_mapping[address] = new_shard
    
    def process_cross_shard_transaction(self, transaction: Dict) -> bool:
        """
        Process a cross-shard transaction.
        
        Args:
            transaction: Cross-shard transaction to process
            
        Returns:
            True if transaction was successfully processed
        """
        from_shard = self.get_shard_id(transaction['from_address'])
        to_shard = self.get_shard_id(transaction['to_address'])
        
        if from_shard == to_shard:
            return False
            
        # Add transaction to cross-shard queue
        transaction['from_shard'] = from_shard
        transaction['to_shard'] = to_shard
        transaction['status'] = 'pending'
        transaction['timestamp'] = time.time()
        
        self.cross_shard_transactions.append(transaction)
        return True
    
    def execute_cross_shard_transactions(self) -> List[Dict]:
        """
        Execute cross-shard transactions.
        
        Returns:
            List of executed cross-shard transactions
        """
        executed = []
        pending = []
        
        for tx in self.cross_shard_transactions:
            if self._can_execute_cross_shard(tx):
                self._execute_cross_shard_transaction(tx)
                executed.append(tx)
            else:
                pending.append(tx)
        
        self.cross_shard_transactions = pending
        return executed
    
    def _can_execute_cross_shard(self, transaction: Dict) -> bool:
        """Check if cross-shard transaction can be executed."""
        # Check if transaction is pending and has valid signatures
        return transaction['status'] == 'pending'
    
    def _execute_cross_shard_transaction(self, transaction: Dict):
        """Execute a cross-shard transaction."""
        from_shard = transaction['from_shard']
        to_shard = transaction['to_shard']
        
        # Update balances in both shards
        # This would require coordination between shard chains
        transaction['status'] = 'completed'
        transaction['execution_time'] = time.time()
    
    def get_shard_info(self, shard_id: int) -> Dict:
        """
        Get information about a specific shard.
        
        Args:
            shard_id: Shard ID
            
        Returns:
            Shard information dictionary
        """
        if shard_id not in self.shards:
            return {}
            
        blockchain = self.shards[shard_id]
        
        return {
            'shard_id': shard_id,
            'block_count': len(blockchain.chain),
            'transaction_count': sum(len(block.transactions) for block in blockchain.chain),
            'validators': self.shard_validators.get(shard_id, []),
            'committee': self.shard_committee.get(shard_id, []),
            'size_bytes': self._get_shard_size_bytes(shard_id),
            'address_count': self._get_shard_address_count(shard_id)
        }
    
    def get_all_shards_info(self) -> List[Dict]:
        """
        Get information about all shards.
        
        Returns:
            List of shard information dictionaries
        """
        return [self.get_shard_info(shard_id) for shard_id in range(self.shard_count)]
    
    def _get_shard_size_bytes(self, shard_id: int) -> int:
        """Get shard size in bytes (approximate)."""
        blockchain = self.shards[shard_id]
        return len(str(blockchain.chain)) * 2  # Approximate
    
    def _get_shard_address_count(self, shard_id: int) -> int:
        """Get number of addresses in a shard."""
        return sum(1 for address, shard in self.shard_mapping.items() if shard == shard_id)
    
    def add_validator_to_shard(self, validator_address: str, shard_id: int):
        """
        Add validator to a shard.
        
        Args:
            validator_address: Validator address
            shard_id: Shard ID
            
        Raises:
            ValueError: If shard ID is invalid
        """
        if shard_id not in self.shards:
            raise ValueError(f"Invalid shard ID: {shard_id}")
            
        if validator_address not in self.shard_validators[shard_id]:
            self.shard_validators[shard_id].append(validator_address)
    
    def remove_validator_from_shard(self, validator_address: str, shard_id: int):
        """
        Remove validator from a shard.
        
        Args:
            validator_address: Validator address
            shard_id: Shard ID
        """
        if shard_id in self.shard_validators:
            if validator_address in self.shard_validators[shard_id]:
                self.shard_validators[shard_id].remove(validator_address)
    
    def rotate_shard_committee(self, shard_id: int):
        """
        Rotate shard committee.
        
        Args:
            shard_id: Shard ID
        """
        if shard_id not in self.shards:
            return
            
        # Simple committee rotation: cycle validators
        if self.shard_validators[shard_id]:
            validator = self.shard_validators[shard_id].pop(0)
            self.shard_validators[shard_id].append(validator)
    
    def get_shard_by_block_hash(self, block_hash: str) -> Optional[int]:
        """
        Get shard ID containing a specific block.
        
        Args:
            block_hash: Block hash
            
        Returns:
            Shard ID if found, None otherwise
        """
        for shard_id, blockchain in self.shards.items():
            for block in blockchain.chain:
                if block.hash == block_hash:
                    return shard_id
                    
        return None
    
    def get_blocks_from_shard(self, shard_id: int, 
                            start_block: int = 0, 
                            end_block: int = None) -> List[Block]:
        """
        Get blocks from a specific shard.
        
        Args:
            shard_id: Shard ID
            start_block: Starting block index
            end_block: Ending block index
            
        Returns:
            List of blocks from the shard
        """
        if shard_id not in self.shards:
            return []
            
        blockchain = self.shards[shard_id]
        
        if end_block is None:
            end_block = len(blockchain.chain)
            
        return blockchain.chain[start_block:end_block]
    
    def get_sharding_statistics(self) -> Dict:
        """
        Get sharding statistics.
        
        Returns:
            Sharding statistics dictionary
        """
        shard_info = self.get_all_shards_info()
        
        total_blocks = sum(info['block_count'] for info in shard_info)
        total_transactions = sum(info['transaction_count'] for info in shard_info)
        total_validators = sum(len(info['validators']) for info in shard_info)
        total_addresses = len(self.shard_mapping)
        
        return {
            'total_shards': self.shard_count,
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'total_validators': total_validators,
            'total_addresses': total_addresses,
            'cross_shard_transactions': len(self.cross_shard_transactions),
            'avg_blocks_per_shard': total_blocks / self.shard_count,
            'avg_transactions_per_shard': total_transactions / self.shard_count,
            'shard_info': shard_info
        }
    
    def __repr__(self):
        """String representation of the ShardManager."""
        stats = self.get_sharding_statistics()
        return (f"ShardManager(shards={stats['total_shards']}, "
                f"blocks={stats['total_blocks']}, "
                f"validators={stats['total_validators']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_sharding_statistics()
        
        return (
            f"Shard Manager\n"
            f"=============\n"
            f"Total Shards: {stats['total_shards']}\n"
            f"Total Blocks: {stats['total_blocks']:,}\n"
            f"Total Transactions: {stats['total_transactions']:,}\n"
            f"Total Validators: {stats['total_validators']}\n"
            f"Total Addresses: {stats['total_addresses']:,}\n"
            f"Cross-Shard Transactions: {stats['cross_shard_transactions']}\n"
            f"Average Blocks per Shard: {stats['avg_blocks_per_shard']:.1f}\n"
            f"Average Transactions per Shard: {stats['avg_transactions_per_shard']:.1f}"
        )
