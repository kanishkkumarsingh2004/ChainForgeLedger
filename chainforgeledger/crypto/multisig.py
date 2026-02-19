"""
ChainForgeLedger Multi-Signature Module

Multi-signature wallet and transaction signing implementation.
"""

from typing import List
from chainforgeledger.crypto.hashing import sha256_hash
from chainforgeledger.crypto.signature import Signature


class MultiSignature:
    """
    Multi-signature implementation for secure transaction validation.
    
    Attributes:
        required_signatures: Number of signatures required to validate
        public_keys: List of authorized public keys
        signatures: Dictionary of signatures keyed by public key
    """
    
    def __init__(self, required_signatures: int, public_keys: List[str]):
        """
        Initialize a multi-signature instance.
        
        Args:
            required_signatures: Number of signatures needed for validation
            public_keys: List of authorized public key addresses
            
        Raises:
            ValueError: If required signatures > number of public keys
        """
        if required_signatures > len(public_keys):
            raise ValueError("Required signatures cannot exceed number of public keys")
            
        self.required_signatures = required_signatures
        self.public_keys = public_keys
        self.signatures = {}
        
    def add_signature(self, public_key: str, signature: str, message: str) -> bool:
        """
        Add a signature to the multi-signature set.
        
        Args:
            public_key: Public key of the signer
            signature: Digital signature
            message: Original message that was signed
            
        Returns:
            True if signature is valid and added successfully
        """
        if public_key not in self.public_keys:
            return False
            
        # Validate the signature
        if not Signature.verify(message, signature, public_key):
            return False
            
        self.signatures[public_key] = signature
        return True
        
    def has_required_signatures(self) -> bool:
        """
        Check if enough valid signatures have been collected.
        
        Returns:
            True if required number of signatures are present
        """
        return len(self.signatures) >= self.required_signatures
        
    def validate_transaction(self, message: str) -> bool:
        """
        Validate all collected signatures against the message.
        
        Args:
            message: Original message to validate against
            
        Returns:
            True if all signatures are valid and required number is met
        """
        if not self.has_required_signatures():
            return False
            
        for public_key, signature in self.signatures.items():
            if not Signature.verify(message, signature, public_key):
                return False
                
        return True
        
    def get_signature_count(self) -> int:
        """Get number of collected signatures."""
        return len(self.signatures)
        
    def get_remaining_signatures_needed(self) -> int:
        """Get number of additional signatures needed."""
        return max(0, self.required_signatures - len(self.signatures))
        
    def get_signed_public_keys(self) -> List[str]:
        """Get list of public keys that have signed."""
        return list(self.signatures.keys())
        
    def get_unsigned_public_keys(self) -> List[str]:
        """Get list of public keys that haven't signed yet."""
        return [pk for pk in self.public_keys if pk not in self.signatures]
        
    def clear_signatures(self):
        """Clear all collected signatures."""
        self.signatures.clear()


class MultiSigWallet:
    """
    Multi-signature wallet implementation.
    
    Attributes:
        address: Multi-signature wallet address
        multisig: MultiSignature instance
        balance: Current wallet balance
    """
    
    def __init__(self, required_signatures: int, public_keys: List[str]):
        """
        Initialize a multi-signature wallet.
        
        Args:
            required_signatures: Number of signatures needed for validation
            public_keys: List of authorized public key addresses
        """
        self.multisig = MultiSignature(required_signatures, public_keys)
        self.address = self._generate_address()
        self.balance = 0.0
        
    def _generate_address(self) -> str:
        """Generate unique address for the multi-signature wallet."""
        # Sort public keys for consistent address generation
        sorted_keys = sorted(self.multisig.public_keys)
        data = f"{self.multisig.required_signatures}:{','.join(sorted_keys)}"
        return sha256_hash(data)
        
    def sign_transaction(self, transaction: dict, private_key: str, public_key: str) -> bool:
        """
        Sign a transaction with a specific private key.
        
        Args:
            transaction: Transaction to sign
            private_key: Private key of the signer
            public_key: Corresponding public key
            
        Returns:
            True if signature is valid and added successfully
        """
        if public_key not in self.multisig.public_keys:
            return False
            
        # Create signature
        transaction_hash = self._hash_transaction(transaction)
        signature = Signature.sign(transaction_hash, private_key)
        
        # Add signature to multi-signature set
        return self.multisig.add_signature(public_key, signature, transaction_hash)
        
    def _hash_transaction(self, transaction: dict) -> str:
        """Generate unique hash for a transaction."""
        data = (
            str(transaction.get('sender', '')) +
            str(transaction.get('receiver', '')) +
            str(transaction.get('amount', '')) +
            str(transaction.get('timestamp', '')) +
            str(transaction.get('fee', ''))
        )
        return sha256_hash(data)
        
    def is_transaction_valid(self, transaction: dict) -> bool:
        """
        Check if transaction has enough valid signatures.
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            True if transaction is valid
        """
        transaction_hash = self._hash_transaction(transaction)
        return self.multisig.validate_transaction(transaction_hash)
        
    def get_wallet_info(self) -> dict:
        """Get detailed information about the wallet."""
        return {
            'address': self.address,
            'required_signatures': self.multisig.required_signatures,
            'total_public_keys': len(self.multisig.public_keys),
            'signed_count': self.multisig.get_signature_count(),
            'remaining_needed': self.multisig.get_remaining_signatures_needed(),
            'signed_keys': self.multisig.get_signed_public_keys(),
            'unsigned_keys': self.multisig.get_unsigned_public_keys(),
            'balance': self.balance
        }
