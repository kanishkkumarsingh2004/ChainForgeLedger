"""
ChainForgeLedger Block Module

Represents a single block in the blockchain.
"""

import time
from typing import List
from chainforgeledger.crypto.hashing import sha256_hash


class Block:
    """
    Represents a single block in the blockchain.
    
    Attributes:
        index: Block position in the chain
        timestamp: Time when block was created
        transactions: List of transactions included in the block
        previous_hash: Hash of the previous block
        hash: Block's own hash
        nonce: Proof of work value (for PoW consensus)
        validator: Validator address (for PoS consensus)
        difficulty: Mining difficulty (for PoW consensus)
    """
    
    def __init__(
        self,
        index: int,
        previous_hash: str,
        transactions: List[dict],
        timestamp: float = None,
        nonce: int = 0,
        validator: str = None,
        difficulty: int = 3
    ):
        """
        Initialize a new Block instance.
        
        Args:
            index: Block position in the chain
            previous_hash: Hash of the previous block
            transactions: List of transactions
            timestamp: Optional timestamp (defaults to current time)
            nonce: Proof of work value
            validator: Validator address
            difficulty: Mining difficulty
        """
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.validator = validator
        self.difficulty = difficulty
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate block hash using SHA-256.
        
        Returns:
            SHA-256 hash of the block
        """
        data = (
            str(self.index) +
            str(self.previous_hash) +
            str(self.transactions) +
            str(self.timestamp) +
            str(self.nonce) +
            str(self.validator or "") +
            str(self.difficulty)
        )
        
        return sha256_hash(data)
    
    def validate_block(self) -> bool:
        """
        Validate the block's hash.
        
        Returns:
            True if the block is valid
        """
        current_hash = self.calculate_hash()
        return current_hash == self.hash
    
    def __repr__(self):
        """String representation of the block."""
        return (
            f"Block(index={self.index}, hash={self.hash[:16]}..., "
            f"transactions={len(self.transactions)}, "
            f"validator={self.validator})"
        )
    
    def __str__(self):
        """String representation for printing."""
        return (
            f"Block {self.index}\n"
            f"==========\n"
            f"Hash: {self.hash}\n"
            f"Previous Hash: {self.previous_hash}\n"
            f"Timestamp: {self.timestamp}\n"
            f"Transactions: {len(self.transactions)}\n"
            f"Nonce: {self.nonce}\n"
            f"Validator: {self.validator}\n"
            f"Difficulty: {self.difficulty}"
        )
