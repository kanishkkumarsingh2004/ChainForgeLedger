"""
ChainForgeLedger Token Standards Module

Custom token standards implementation:
- KK-20: Fungible token standard (similar to ERC-20)
- KK-721: Non-fungible token standard (similar to ERC-721)
"""

from typing import Dict, List, Optional, Union
from chainforgeledger.crypto.hashing import sha256_hash
from chainforgeledger.crypto.signature import Signature
from chainforgeledger.storage.database import Database


class KK20Token:
    """
    KK-20 Fungible Token Standard Implementation
    
    A standard interface for fungible tokens with transfer, balance tracking,
    and allowance functionality.
    """
    
    def __init__(self, name: str, symbol: str, decimals: int, total_supply: int):
        """
        Initialize a KK-20 token.
        
        Args:
            name: Token name
            symbol: Token symbol
            decimals: Number of decimal places
            total_supply: Total token supply
        """
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.total_supply = total_supply
        self.balances = {}
        self.allowances = {}
        self.token_id = self._generate_token_id()
        
    def _generate_token_id(self) -> str:
        """Generate unique token identifier."""
        data = f"{self.name}:{self.symbol}:{self.decimals}:{self.total_supply}"
        return sha256_hash(data)
        
    def mint(self, to_address: str, amount: int) -> bool:
        """
        Mint new tokens and add to recipient's balance.
        
        Args:
            to_address: Recipient address
            amount: Amount to mint
            
        Returns:
            True if minting was successful
        """
        if amount <= 0:
            return False
            
        if to_address not in self.balances:
            self.balances[to_address] = 0
            
        self.balances[to_address] += amount
        self.total_supply += amount
        return True
        
    def burn(self, from_address: str, amount: int) -> bool:
        """
        Burn tokens and remove from owner's balance.
        
        Args:
            from_address: Address to burn from
            amount: Amount to burn
            
        Returns:
            True if burning was successful
        """
        if amount <= 0 or from_address not in self.balances:
            return False
            
        if self.balances[from_address] < amount:
            return False
            
        self.balances[from_address] -= amount
        self.total_supply -= amount
        return True
        
    def transfer(self, from_address: str, to_address: str, amount: int, signature: str) -> bool:
        """
        Transfer tokens between addresses.
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount: Amount to transfer
            signature: Sender's digital signature
            
        Returns:
            True if transfer was successful
        """
        if not self._validate_transaction(from_address, to_address, amount, signature):
            return False
            
        if self.balances.get(from_address, 0) < amount:
            return False
            
        self.balances[from_address] -= amount
        if to_address not in self.balances:
            self.balances[to_address] = 0
        self.balances[to_address] += amount
        return True
        
    def approve(self, owner_address: str, spender_address: str, amount: int, signature: str) -> bool:
        """
        Approve a spender to spend tokens on owner's behalf.
        
        Args:
            owner_address: Token owner address
            spender_address: Spender address
            amount: Amount to approve
            signature: Owner's digital signature
            
        Returns:
            True if approval was successful
        """
        if not self._validate_approval(owner_address, spender_address, amount, signature):
            return False
            
        if owner_address not in self.allowances:
            self.allowances[owner_address] = {}
            
        self.allowances[owner_address][spender_address] = amount
        return True
        
    def transfer_from(self, spender_address: str, from_address: str, to_address: str, amount: int) -> bool:
        """
        Transfer tokens from one address to another using allowance.
        
        Args:
            spender_address: Spender address
            from_address: Source address
            to_address: Destination address
            amount: Amount to transfer
            
        Returns:
            True if transfer was successful
        """
        if from_address not in self.allowances or spender_address not in self.allowances[from_address]:
            return False
            
        if self.allowances[from_address][spender_address] < amount:
            return False
            
        if self.balances.get(from_address, 0) < amount:
            return False
            
        self.allowances[from_address][spender_address] -= amount
        self.balances[from_address] -= amount
        if to_address not in self.balances:
            self.balances[to_address] = 0
        self.balances[to_address] += amount
        return True
        
    def get_balance(self, address: str) -> int:
        """Get balance of an address."""
        return self.balances.get(address, 0)
        
    def get_allowance(self, owner_address: str, spender_address: str) -> int:
        """Get allowance for a spender from an owner."""
        if owner_address not in self.allowances or spender_address not in self.allowances[owner_address]:
            return 0
        return self.allowances[owner_address][spender_address]
        
    def _validate_transaction(self, from_address: str, to_address: str, amount: int, signature: str) -> bool:
        """Validate transaction parameters and signature."""
        if amount <= 0 or not from_address or not to_address:
            return False
            
        # Validate signature
        transaction_data = f"{self.token_id}:transfer:{from_address}:{to_address}:{amount}"
        return Signature.verify(transaction_data, signature, from_address)
        
    def _validate_approval(self, owner_address: str, spender_address: str, amount: int, signature: str) -> bool:
        """Validate approval parameters and signature."""
        if amount <= 0 or not owner_address or not spender_address:
            return False
            
        # Validate signature
        approval_data = f"{self.token_id}:approve:{owner_address}:{spender_address}:{amount}"
        return Signature.verify(approval_data, signature, owner_address)


class KK721Token:
    """
    KK-721 Non-Fungible Token Standard Implementation
    
    A standard interface for non-fungible tokens with unique identifiers,
    ownership tracking, and metadata support.
    """
    
    def __init__(self, name: str, symbol: str):
        """
        Initialize a KK-721 token.
        
        Args:
            name: Token name
            symbol: Token symbol
        """
        self.name = name
        self.symbol = symbol
        self.token_id = self._generate_token_id()
        self.token_owners = {}
        self.owner_tokens = {}
        self.token_metadata = {}
        self.token_uris = {}
        self.allowances = {}
        self.next_token_id = 1
        
    def _generate_token_id(self) -> str:
        """Generate unique token collection identifier."""
        data = f"{self.name}:{self.symbol}"
        return sha256_hash(data)
        
    def mint(self, to_address: str, metadata: Optional[Dict] = None, token_uri: Optional[str] = None) -> int:
        """
        Mint a new unique token.
        
        Args:
            to_address: Recipient address
            metadata: Optional token metadata
            token_uri: Optional token URI
            
        Returns:
            New token ID if successful, 0 otherwise
        """
        if not to_address:
            return 0
            
        token_id = self.next_token_id
        self.next_token_id += 1
        
        self.token_owners[token_id] = to_address
        
        if to_address not in self.owner_tokens:
            self.owner_tokens[to_address] = []
        self.owner_tokens[to_address].append(token_id)
        
        if metadata:
            self.token_metadata[token_id] = metadata
            
        if token_uri:
            self.token_uris[token_id] = token_uri
            
        return token_id
        
    def transfer_from(self, from_address: str, to_address: str, token_id: int, signature: str) -> bool:
        """
        Transfer ownership of a token.
        
        Args:
            from_address: Current owner address
            to_address: New owner address
            token_id: Token ID to transfer
            signature: Sender's digital signature
            
        Returns:
            True if transfer was successful
        """
        if not self._validate_transfer(from_address, to_address, token_id, signature):
            return False
            
        if self.token_owners.get(token_id) != from_address:
            return False
            
        # Transfer ownership
        self.token_owners[token_id] = to_address
        self.owner_tokens[from_address].remove(token_id)
        
        if to_address not in self.owner_tokens:
            self.owner_tokens[to_address] = []
        self.owner_tokens[to_address].append(token_id)
        
        return True
        
    def approve(self, owner_address: str, spender_address: str, token_id: int, signature: str) -> bool:
        """
        Approve a spender to transfer a specific token.
        
        Args:
            owner_address: Token owner address
            spender_address: Spender address
            token_id: Token ID to approve
            signature: Owner's digital signature
            
        Returns:
            True if approval was successful
        """
        if not self._validate_approval(owner_address, spender_address, token_id, signature):
            return False
            
        if self.token_owners.get(token_id) != owner_address:
            return False
            
        self.allowances[token_id] = spender_address
        return True
        
    def get_owner(self, token_id: int) -> Optional[str]:
        """Get owner of a token."""
        return self.token_owners.get(token_id)
        
    def get_tokens_by_owner(self, address: str) -> List[int]:
        """Get all tokens owned by an address."""
        return self.owner_tokens.get(address, [])
        
    def get_balance(self, address: str) -> int:
        """Get number of tokens owned by an address."""
        return len(self.get_tokens_by_owner(address))
        
    def get_metadata(self, token_id: int) -> Optional[Dict]:
        """Get metadata for a token."""
        return self.token_metadata.get(token_id)
        
    def get_token_uri(self, token_id: int) -> Optional[str]:
        """Get token URI."""
        return self.token_uris.get(token_id)
        
    def get_approval(self, token_id: int) -> Optional[str]:
        """Get approved spender for a token."""
        return self.allowances.get(token_id)
        
    def _validate_transfer(self, from_address: str, to_address: str, token_id: int, signature: str) -> bool:
        """Validate transfer parameters and signature."""
        if not from_address or not to_address or token_id <= 0:
            return False
            
        # Validate signature
        transfer_data = f"{self.token_id}:transfer:{from_address}:{to_address}:{token_id}"
        return Signature.verify(transfer_data, signature, from_address)
        
    def _validate_approval(self, owner_address: str, spender_address: str, token_id: int, signature: str) -> bool:
        """Validate approval parameters and signature."""
        if not owner_address or not spender_address or token_id <= 0:
            return False
            
        # Validate signature
        approval_data = f"{self.token_id}:approve:{owner_address}:{spender_address}:{token_id}"
        return Signature.verify(approval_data, signature, owner_address)


class TokenFactory:
    """
    Factory for creating token instances.
    """
    
    @staticmethod
    def create_kk20_token(name: str, symbol: str, decimals: int, total_supply: int) -> KK20Token:
        """Create a KK-20 fungible token."""
        return KK20Token(name, symbol, decimals, total_supply)
        
    @staticmethod
    def create_kk721_token(name: str, symbol: str) -> KK721Token:
        """Create a KK-721 non-fungible token."""
        return KK721Token(name, symbol)
        
    @staticmethod
    def create_native_coin(name: str = "ChainForge Coin", symbol: str = "CFC", 
                        decimals: int = 8, initial_supply: int = 100000000):
        """Create a native cryptocurrency instance."""
        from chainforgeledger.tokenomics.native import NativeCoin
        return NativeCoin(name, symbol, decimals, initial_supply)
        
    @staticmethod
    def create_stablecoin(name: str, symbol: str, peg_currency: str,
                        target_price: float = 1.0, collateral_ratio: float = 1.5,
                        minting_fee: float = 0.01, redemption_fee: float = 0.01):
        """Create a stablecoin instance."""
        from chainforgeledger.tokenomics.stablecoin import Stablecoin
        return Stablecoin(name, symbol, peg_currency, target_price, collateral_ratio,
                        minting_fee, redemption_fee)
        
    @staticmethod
    def load_token_from_storage(database: Database, token_id: str):
        """Load token from storage."""
        token_data = database.get_token_data(token_id)
        if not token_data:
            return None
            
        token_type = token_data.get('type')
        if token_type == 'KK20':
            token = KK20Token(
                token_data['name'],
                token_data['symbol'],
                token_data['decimals'],
                token_data['total_supply']
            )
            token.balances = token_data.get('balances', {})
            token.allowances = token_data.get('allowances', {})
            return token
        elif token_type == 'KK721':
            token = KK721Token(
                token_data['name'],
                token_data['symbol']
            )
            token.token_owners = token_data.get('token_owners', {})
            token.owner_tokens = token_data.get('owner_tokens', {})
            token.token_metadata = token_data.get('token_metadata', {})
            token.token_uris = token_data.get('token_uris', {})
            token.allowances = token_data.get('allowances', {})
            token.next_token_id = token_data.get('next_token_id', 1)
            return token
        elif token_type == 'NATIVE':
            from chainforgeledger.tokenomics.native import NativeCoin
            token = NativeCoin(
                token_data['name'],
                token_data['symbol'],
                token_data['decimals'],
                token_data['total_supply']
            )
            token.balances = token_data.get('balances', {})
            token.staking_balances = token_data.get('staking_balances', {})
            token.treasury_address = token_data.get('treasury_address')
            token.treasury_balance = token_data.get('treasury_balance', 0)
            token.supply_control = token_data.get('supply_control', {})
            return token
        elif token_type == 'STABLE':
            from chainforgeledger.tokenomics.stablecoin import Stablecoin
            token = Stablecoin(
                token_data['name'],
                token_data['symbol'],
                token_data['peg_currency'],
                token_data['target_price'],
                token_data['collateral_ratio'],
                token_data['minting_fee'],
                token_data['redemption_fee']
            )
            token.total_supply = token_data.get('total_supply', 0)
            token.circulating_supply = token_data.get('circulating_supply', 0)
            token.collateral_reserves = token_data.get('collateral_reserves', {})
            token.collateral_tokens = token_data.get('collateral_tokens', [])
            token.price_oracle = token_data.get('price_oracle', {})
            token.minting_history = token_data.get('minting_history', [])
            token.redemption_history = token_data.get('redemption_history', [])
            token.collateral_history = token_data.get('collateral_history', [])
            return token
            
        return None
        
    @staticmethod
    def save_token_to_storage(database: Database, token):
        """Save token to storage."""
        token_data = {
            'token_id': token.token_id,
            'name': token.name,
            'symbol': token.symbol
        }
        
        if isinstance(token, KK20Token):
            token_data['type'] = 'KK20'
            token_data['decimals'] = token.decimals
            token_data['total_supply'] = token.total_supply
            token_data['balances'] = token.balances
            token_data['allowances'] = token.allowances
        elif isinstance(token, KK721Token):
            token_data['type'] = 'KK721'
            token_data['token_owners'] = token.token_owners
            token_data['owner_tokens'] = token.owner_tokens
            token_data['token_metadata'] = token.token_metadata
            token_data['token_uris'] = token.token_uris
            token_data['allowances'] = token.allowances
            token_data['next_token_id'] = token.next_token_id
        elif hasattr(token, 'supply_control'):  # NativeCoin
            token_data['type'] = 'NATIVE'
            token_data['decimals'] = token.decimals
            token_data['total_supply'] = token.total_supply
            token_data['balances'] = token.balances
            token_data['staking_balances'] = token.staking_balances
            token_data['treasury_address'] = token.treasury_address
            token_data['treasury_balance'] = token.treasury_balance
            token_data['supply_control'] = token.supply_control
        elif hasattr(token, 'peg_currency'):  # Stablecoin
            token_data['type'] = 'STABLE'
            token_data['peg_currency'] = token.peg_currency
            token_data['target_price'] = token.target_price
            token_data['collateral_ratio'] = token.collateral_ratio
            token_data['minting_fee'] = token.minting_fee
            token_data['redemption_fee'] = token.redemption_fee
            token_data['total_supply'] = token.total_supply
            token_data['circulating_supply'] = token.circulating_supply
            token_data['collateral_reserves'] = token.collateral_reserves
            token_data['collateral_tokens'] = token.collateral_tokens
            token_data['price_oracle'] = token.price_oracle
            token_data['minting_history'] = token.minting_history
            token_data['redemption_history'] = token.redemption_history
            token_data['collateral_history'] = token.collateral_history
            
        database.save_token_data(token.token_id, token_data)
