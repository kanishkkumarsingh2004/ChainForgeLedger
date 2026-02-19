"""
ChainForgeLedger Transaction Module

Transaction management and validation.
"""

import time
from chainforgeledger.crypto.hashing import sha256_hash

class Transaction:
    """
    Represents a blockchain transaction.
    
    Attributes:
        sender: Sender address
        receiver: Receiver address
        amount: Transaction amount
        timestamp: Transaction timestamp
        signature: Digital signature
        fee: Transaction fee
        data: Additional transaction data
    """
    
    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: float,
        timestamp: float = None,
        signature: str = None,
        fee: float = 0.0,
        data: dict = None
    ):
        """
        Initialize a new Transaction instance.
        
        Args:
            sender: Sender address
            receiver: Receiver address
            amount: Transaction amount
            timestamp: Optional timestamp (defaults to current time)
            signature: Optional digital signature
            fee: Transaction fee
            data: Additional transaction data
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.fee = fee
        self.data = data or {}
        self.transaction_id = self.calculate_id()
    
    def calculate_id(self) -> str:
        """
        Calculate transaction hash (ID).
        
        Returns:
            SHA-256 hash of transaction
        """
        data = (
            str(self.sender) +
            str(self.receiver) +
            str(self.amount) +
            str(self.timestamp) +
            str(self.fee) +
            str(self.data)
        )
        
        return sha256_hash(data)
    
    def sign_transaction(self, private_key: str) -> bool:
        """
        Sign the transaction with sender's private key.
        
        Args:
            private_key: Sender's private key
            
        Returns:
            True if signed successfully
        """
        # TODO: Implement signature creation
        self.signature = f"signature_{self.transaction_id}"
        return True
    
    def validate_transaction(self) -> bool:
        """
        Validate the transaction.
        
        Returns:
            True if transaction is valid
        """
        # Check basic requirements
        if not self.sender or not self.receiver:
            return False
            
        if self.amount <= 0:
            return False
            
        if self.fee < 0:
            return False
            
        if self.sender == self.receiver:
            return False
            
        # Check signature
        if not self.signature:
            return False
            
        return True
    
    def is_valid_signature(self) -> bool:
        """
        Validate transaction signature.
        
        Returns:
            True if signature is valid
        """
        # TODO: Implement signature validation
        return bool(self.signature)
    
    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary.
        
        Returns:
            Dictionary representation of transaction
        """
        return {
            "transaction_id": self.transaction_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "fee": self.fee,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """
        Create transaction from dictionary.
        
        Args:
            data: Transaction data
            
        Returns:
            Transaction instance
        """
        return cls(
            sender=data.get("sender", ""),
            receiver=data.get("receiver", ""),
            amount=data.get("amount", 0.0),
            timestamp=data.get("timestamp"),
            signature=data.get("signature"),
            fee=data.get("fee", 0.0),
            data=data.get("data", {})
        )
    
    def __repr__(self):
        """String representation of transaction."""
        return (
            f"Transaction(id={self.transaction_id[:16]}..., "
            f"{self.sender} -> {self.receiver}, "
            f"{self.amount})"
        )
    
    def __str__(self):
        """String representation for printing."""
        return (
            f"Transaction: {self.transaction_id}\n"
            f"From: {self.sender}\n"
            f"To: {self.receiver}\n"
            f"Amount: {self.amount}\n"
            f"Fee: {self.fee}\n"
            f"Timestamp: {self.timestamp}\n"
            f"Signature: {self.signature}"
        )
