"""
ChainForgeLedger Native Coin Implementation

Implements the native cryptocurrency for the blockchain.
"""

from typing import Dict
from chainforgeledger.crypto.hashing import sha256_hash
from chainforgeledger.crypto.signature import Signature


class NativeCoin:
    """
    Native cryptocurrency implementation.
    
    Attributes:
        name: Coin name
        symbol: Coin symbol
        decimals: Number of decimal places
        total_supply: Total coin supply
        balances: Account balances
        staking_balances: Staking balances
        treasury: Treasury address and balance
        supply_control: Supply control parameters
    """
    
    def __init__(self, name: str = "ChainForge Coin", symbol: str = "CFC", 
                 decimals: int = 8, initial_supply: int = 100000000):
        """
        Initialize a NativeCoin instance.
        
        Args:
            name: Coin name
            symbol: Coin symbol
            decimals: Number of decimal places
            initial_supply: Initial coin supply
        """
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.total_supply = initial_supply
        self.balances: Dict[str, int] = {}
        self.staking_balances: Dict[str, int] = {}
        self.treasury_address = self._generate_treasury_address()
        self.treasury_balance = 0
        self.supply_control = {
            'inflation_rate': 0.02,
            'max_supply': 210000000,
            'block_reward': 50,
            'halving_interval': 210000,
            'transaction_fee_percentage': 0.001
        }
        self.token_id = self._generate_token_id()
        self._init_initial_distribution()
        
    def _generate_token_id(self) -> str:
        """Generate unique token identifier."""
        data = f"{self.name}:{self.symbol}:{self.decimals}:{self.total_supply}"
        return sha256_hash(data)
    
    def _generate_treasury_address(self) -> str:
        """Generate unique treasury address."""
        data = f"{self.name}:{self.symbol}:{self.decimals}"
        return sha256_hash(data)[:32]
    
    def _init_initial_distribution(self):
        """Initialize initial coin distribution."""
        # Distribute initial supply to treasury
        self.treasury_balance = self.total_supply
    
    def transfer(self, from_address: str, to_address: str, amount: int, 
                signature: str) -> bool:
        """
        Transfer coins between addresses.
        
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
            
        if from_address == self.treasury_address:
            if self.treasury_balance < amount:
                return False
            self.treasury_balance -= amount
        else:
            if self.balances.get(from_address, 0) < amount:
                return False
            self.balances[from_address] -= amount
            
        if to_address == self.treasury_address:
            self.treasury_balance += amount
        else:
            if to_address not in self.balances:
                self.balances[to_address] = 0
            self.balances[to_address] += amount
            
        return True
    
    def stake(self, address: str, amount: int, signature: str) -> bool:
        """
        Stake coins.
        
        Args:
            address: Staker address
            amount: Amount to stake
            signature: Staker's digital signature
            
        Returns:
            True if staking was successful
        """
        if not self._validate_staking(address, amount, signature):
            return False
            
        if self.balances.get(address, 0) < amount:
            return False
            
        self.balances[address] -= amount
        
        if address not in self.staking_balances:
            self.staking_balances[address] = 0
        self.staking_balances[address] += amount
        
        return True
    
    def unstake(self, address: str, amount: int, signature: str) -> bool:
        """
        Unstake coins.
        
        Args:
            address: Staker address
            amount: Amount to unstake
            signature: Staker's digital signature
            
        Returns:
            True if unstaking was successful
        """
        if not self._validate_unstaking(address, amount, signature):
            return False
            
        if self.staking_balances.get(address, 0) < amount:
            return False
            
        self.staking_balances[address] -= amount
        self.balances[address] += amount
        
        return True
    
    def mint(self, to_address: str, amount: int) -> bool:
        """
        Mint new coins.
        
        Args:
            to_address: Recipient address
            amount: Amount to mint
            
        Returns:
            True if minting was successful
        """
        if amount <= 0:
            return False
            
        # Check supply limit
        if self.total_supply + amount > self.supply_control['max_supply']:
            return False
            
        self.total_supply += amount
        
        if to_address == self.treasury_address:
            self.treasury_balance += amount
        else:
            if to_address not in self.balances:
                self.balances[to_address] = 0
            self.balances[to_address] += amount
            
        return True
    
    def burn(self, from_address: str, amount: int, signature: str) -> bool:
        """
        Burn coins.
        
        Args:
            from_address: Address to burn from
            amount: Amount to burn
            signature: Owner's digital signature
            
        Returns:
            True if burning was successful
        """
        if not self._validate_burn(from_address, amount, signature):
            return False
            
        if from_address == self.treasury_address:
            if self.treasury_balance < amount:
                return False
            self.treasury_balance -= amount
        else:
            if self.balances.get(from_address, 0) < amount:
                return False
            self.balances[from_address] -= amount
            
        self.total_supply -= amount
        
        return True
    
    def get_balance(self, address: str) -> int:
        """
        Get balance of an address.
        
        Args:
            address: Address to check
            
        Returns:
            Balance including both regular and staking balances
        """
        if address == self.treasury_address:
            return self.treasury_balance
            
        regular = self.balances.get(address, 0)
        staking = self.staking_balances.get(address, 0)
        return regular + staking
    
    def get_regular_balance(self, address: str) -> int:
        """
        Get regular (non-staking) balance of an address.
        
        Args:
            address: Address to check
            
        Returns:
            Regular balance
        """
        if address == self.treasury_address:
            return self.treasury_balance
            
        return self.balances.get(address, 0)
    
    def get_staking_balance(self, address: str) -> int:
        """
        Get staking balance of an address.
        
        Args:
            address: Address to check
            
        Returns:
            Staking balance
        """
        if address == self.treasury_address:
            return 0
            
        return self.staking_balances.get(address, 0)
    
    def get_treasury_balance(self) -> int:
        """
        Get treasury balance.
        
        Returns:
            Treasury balance
        """
        return self.treasury_balance
    
    def distribute_block_reward(self, block_height: int, validator_address: str, 
                               transaction_fees: int) -> bool:
        """
        Distribute block reward.
        
        Args:
            block_height: Current block height
            validator_address: Validator address
            transaction_fees: Transaction fees collected in this block
            
        Returns:
            True if reward distribution was successful
        """
        # Calculate reward with halving
        reward = self._calculate_block_reward(block_height)
        total_reward = reward + transaction_fees
        
        # Distribute reward
        if validator_address == self.treasury_address:
            self.treasury_balance += total_reward
        else:
            if validator_address not in self.balances:
                self.balances[validator_address] = 0
            self.balances[validator_address] += total_reward
            
        return True
    
    def _calculate_block_reward(self, block_height: int) -> int:
        """
        Calculate block reward with halving.
        
        Args:
            block_height: Current block height
            
        Returns:
            Block reward
        """
        halvings = block_height // self.supply_control['halving_interval']
        reward = self.supply_control['block_reward'] / (2 ** halvings)
        
        return int(reward)
    
    def _validate_transaction(self, from_address: str, to_address: str, 
                             amount: int, signature: str) -> bool:
        """Validate transaction parameters and signature."""
        if amount <= 0 or not from_address or not to_address:
            return False
            
        # Validate signature
        transaction_data = f"{self.symbol}:transfer:{from_address}:{to_address}:{amount}"
        return Signature.verify(transaction_data, signature, from_address)
    
    def _validate_staking(self, address: str, amount: int, signature: str) -> bool:
        """Validate staking parameters and signature."""
        if amount <= 0 or not address:
            return False
            
        # Validate signature
        staking_data = f"{self.symbol}:stake:{address}:{amount}"
        return Signature.verify(staking_data, signature, address)
    
    def _validate_unstaking(self, address: str, amount: int, signature: str) -> bool:
        """Validate unstaking parameters and signature."""
        if amount <= 0 or not address:
            return False
            
        # Validate signature
        unstaking_data = f"{self.symbol}:unstake:{address}:{amount}"
        return Signature.verify(unstaking_data, signature, address)
    
    def _validate_burn(self, address: str, amount: int, signature: str) -> bool:
        """Validate burn parameters and signature."""
        if amount <= 0 or not address:
            return False
            
        # Validate signature
        burn_data = f"{self.symbol}:burn:{address}:{amount}"
        return Signature.verify(burn_data, signature, address)
    
    def get_supply_info(self) -> Dict:
        """
        Get supply information.
        
        Returns:
            Supply information dictionary
        """
        circulating_supply = self.total_supply - self.treasury_balance
        staking_total = sum(self.staking_balances.values())
        
        return {
            'name': self.name,
            'symbol': self.symbol,
            'decimals': self.decimals,
            'total_supply': self.total_supply,
            'circulating_supply': circulating_supply,
            'treasury_balance': self.treasury_balance,
            'staking_total': staking_total,
            'max_supply': self.supply_control['max_supply'],
            'inflation_rate': self.supply_control['inflation_rate']
        }
    
    def get_tokenomics_info(self) -> Dict:
        """
        Get tokenomics information.
        
        Returns:
            Tokenomics information dictionary
        """
        return {
            'block_reward': self.supply_control['block_reward'],
            'halving_interval': self.supply_control['halving_interval'],
            'transaction_fee_percentage': self.supply_control['transaction_fee_percentage'],
            'inflation_rate': self.supply_control['inflation_rate'],
            'max_supply': self.supply_control['max_supply']
        }
    
    def set_block_reward(self, reward: int):
        """
        Set block reward.
        
        Args:
            reward: New block reward
            
        Raises:
            ValueError: If reward is invalid
        """
        if reward < 0:
            raise ValueError("Block reward cannot be negative")
            
        self.supply_control['block_reward'] = reward
    
    def set_halving_interval(self, interval: int):
        """
        Set halving interval.
        
        Args:
            interval: New halving interval
            
        Raises:
            ValueError: If interval is invalid
        """
        if interval <= 0:
            raise ValueError("Halving interval must be positive")
            
        self.supply_control['halving_interval'] = interval
    
    def set_transaction_fee_percentage(self, percentage: float):
        """
        Set transaction fee percentage.
        
        Args:
            percentage: New fee percentage (0.0 to 1.0)
            
        Raises:
            ValueError: If percentage is invalid
        """
        if percentage < 0 or percentage > 1:
            raise ValueError("Fee percentage must be between 0 and 1")
            
        self.supply_control['transaction_fee_percentage'] = percentage
    
    def set_inflation_rate(self, rate: float):
        """
        Set inflation rate.
        
        Args:
            rate: New inflation rate (0.0 to 1.0)
            
        Raises:
            ValueError: If rate is invalid
        """
        if rate < 0 or rate > 1:
            raise ValueError("Inflation rate must be between 0 and 1")
            
        self.supply_control['inflation_rate'] = rate
    
    def __repr__(self):
        """String representation of the NativeCoin."""
        return f"NativeCoin(name={self.name}, symbol={self.symbol}, supply={self.total_supply})"
    
    def __str__(self):
        """String representation for printing."""
        supply_info = self.get_supply_info()
        tokenomics = self.get_tokenomics_info()
        
        return (
            f"{self.name} ({self.symbol})\n"
            f"==================\n"
            f"Decimals: {self.decimals}\n"
            f"Total Supply: {supply_info['total_supply']:,}\n"
            f"Circulating Supply: {supply_info['circulating_supply']:,}\n"
            f"Treasury Balance: {supply_info['treasury_balance']:,}\n"
            f"Staking Total: {supply_info['staking_total']:,}\n"
            f"Max Supply: {supply_info['max_supply']:,}\n"
            f"Block Reward: {tokenomics['block_reward']}\n"
            f"Halving Interval: {tokenomics['halving_interval']:,} blocks\n"
            f"Transaction Fee: {tokenomics['transaction_fee_percentage']:.2%}\n"
            f"Inflation Rate: {tokenomics['inflation_rate']:.2%}"
        )
