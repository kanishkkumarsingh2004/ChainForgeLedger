"""
ChainForgeLedger Mnemonic Module

BIP-39 style mnemonic phrase generation and wallet recovery.
"""

from typing import Optional
from chainforgeledger.crypto.keys import KeyPair
from chainforgeledger.crypto.hashing import sha256_hash_bytes


# BIP-39 English wordlist (first 2048 words for demonstration)
# In a real implementation, this would be the complete 2048 word list
BIP39_WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
    "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advantage", "adventure", "advice", "aerobic", "affair", "afford", "afraid", "again",
    "age", "agent", "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album",
    "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone", "along", "aloud",
    "alpha", "already", "also", "altitude", "always", "amateur", "amazing", "among", "amount", "amused",
    "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce", "annual",
    "another", "answer", "antenna", "antique", "anxiety", "any", "apart", "apology", "appear", "apple",
    "approve", "april", "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor",
    # Additional words would be included in a complete implementation
]


class MnemonicGenerator:
    """
    BIP-39 style mnemonic phrase generator and validator.
    
    Attributes:
        word_count: Number of words in the mnemonic (12, 15, 18, 21, or 24)
    """
    
    def __init__(self, word_count: int = 12):
        """
        Initialize a mnemonic generator.
        
        Args:
            word_count: Number of words (12, 15, 18, 21, or 24)
            
        Raises:
            ValueError: If word count is not a valid BIP-39 length
        """
        if word_count not in [12, 15, 18, 21, 24]:
            raise ValueError("Word count must be 12, 15, 18, 21, or 24")
            
        self.word_count = word_count
        
    def generate(self, entropy: Optional[bytes] = None) -> str:
        """
        Generate a mnemonic phrase.
        
        Args:
            entropy: Optional pre-generated entropy bytes
            
        Returns:
            Space-separated mnemonic phrase
        """
        entropy_length = self._get_entropy_length()
        
        if entropy is None:
            import os
            entropy = os.urandom(entropy_length // 8)
        
        checksum = self._generate_checksum(entropy)
        combined = (int.from_bytes(entropy, 'big') << len(checksum)) | int(checksum, 2)
        
        mnemonic = []
        for i in range(self.word_count):
            index = (combined >> (11 * (self.word_count - 1 - i))) & 0x7FF
            mnemonic.append(BIP39_WORDLIST[index])
            
        return ' '.join(mnemonic)
        
    def _get_entropy_length(self) -> int:
        """Get entropy length in bits based on word count."""
        return {
            12: 128,
            15: 160,
            18: 192,
            21: 224,
            24: 256
        }[self.word_count]
        
    def _generate_checksum(self, entropy: bytes) -> str:
        """Generate checksum from entropy."""
        entropy_length = len(entropy) * 8
        checksum_length = entropy_length // 32
        
        hash_bytes = sha256_hash_bytes(entropy)
        hash_bits = bin(int.from_bytes(hash_bytes, 'big'))[2:].zfill(256)
        
        return hash_bits[:checksum_length]
        
    def validate(self, mnemonic: str) -> bool:
        """
        Validate a mnemonic phrase.
        
        Args:
            mnemonic: Space-separated mnemonic phrase
            
        Returns:
            True if mnemonic is valid
        """
        words = mnemonic.split()
        if len(words) not in [12, 15, 18, 21, 24]:
            return False
            
        for word in words:
            if word not in BIP39_WORDLIST:
                return False
                
        try:
            self._mnemonic_to_entropy(mnemonic)
            return True
        except:
            return False
            
    def _mnemonic_to_entropy(self, mnemonic: str) -> bytes:
        """Convert mnemonic phrase to entropy bytes."""
        words = mnemonic.split()
        word_count = len(words)
        entropy_length = word_count * 11
        
        combined = 0
        for word in words:
            index = BIP39_WORDLIST.index(word)
            combined = (combined << 11) | index
            
        checksum_length = word_count // 3
        checksum = combined & ((1 << checksum_length) - 1)
        entropy_bits = combined >> checksum_length
        entropy_bytes = entropy_bits.to_bytes(entropy_length // 8, 'big')
        
        # Verify checksum
        calculated_checksum = self._generate_checksum(entropy_bytes)
        if bin(checksum)[2:].zfill(checksum_length) != calculated_checksum:
            raise ValueError("Invalid checksum")
            
        return entropy_bytes
        
    def to_seed(self, mnemonic: str, passphrase: str = "") -> bytes:
        """
        Convert mnemonic to seed using PBKDF2.
        
        Args:
            mnemonic: Mnemonic phrase
            passphrase: Optional passphrase
            
        Returns:
            64-byte seed for key derivation
        """
        from chainforgeledger.utils.crypto import CryptoUtils
        
        salt = f"mnemonic{passphrase}"
        iterations = 2048
        key_length = 64
        
        # Use custom PBKDF2 implementation (uses SHA-256 for consistency)
        hex_seed = CryptoUtils.pbkdf2(mnemonic, salt, iterations, key_length)
        # Convert hex string to bytes, ensuring we have exactly 64 bytes
        seed = bytes.fromhex(hex_seed)
        if len(seed) < key_length:
            # Pad with zeros if necessary
            seed = seed.ljust(key_length, b'\x00')
        elif len(seed) > key_length:
            # Truncate if longer
            seed = seed[:key_length]
            
        return seed
        
    def generate_keys_from_mnemonic(self, mnemonic: str, passphrase: str = "") -> KeyPair:
        """
        Generate a key pair from a mnemonic phrase.
        
        Args:
            mnemonic: Mnemonic phrase
            passphrase: Optional passphrase
            
        Returns:
            KeyPair object with private and public keys
        """
        seed = self.to_seed(mnemonic, passphrase)
        private_key, public_key = self._generate_keys_from_seed(seed)
        return KeyPair(private_key, public_key)
        
    def _generate_keys_from_seed(self, seed: bytes) -> tuple:
        """Generate key pair from seed using HMAC-SHA256 (since SHA-512 is not implemented)."""
        # This is a simplified implementation - in a real system,
        # BIP-32 derivation would be used
        from chainforgeledger.crypto.hashing import sha256_hash_bytes
        
        # Use HMAC-SHA256 to generate private key (since we don't have SHA-512 implementation)
        # Create HMAC object with key and message
        key = b"ChainForgeLedger"
        # HMAC-SHA256 implementation using our custom SHA-256
        # Note: This is a simplified HMAC implementation
        if len(key) > 64:
            key = sha256_hash_bytes(key)
        elif len(key) < 64:
            key = key + b'\x00' * (64 - len(key))
            
        o_key_pad = bytes([x ^ 0x5c for x in key])
        i_key_pad = bytes([x ^ 0x36 for x in key])
        
        hmac_result = sha256_hash_bytes(o_key_pad + sha256_hash_bytes(i_key_pad + seed))
        private_key = int.from_bytes(hmac_result[:32], 'big')
        
        # Generate public key from private key
        from chainforgeledger.crypto.hashing import scalar_mult, G
        public_key = scalar_mult(private_key, G)
        
        return private_key, public_key
