"""
ChainForgeLedger Tokenomics Module
"""

from typing import Dict, Any


class Tokenomics:
    """
    Tokenomics system for managing cryptocurrency supply, distribution, and economics.
    """
    
    def __init__(self, total_supply: int = 1000000000):
        """
        Initialize tokenomics system.
        
        Args:
            total_supply: Total token supply
        """
        self.total_supply = total_supply
        self.current_supply = total_supply
        self.staking_rewards_pool = int(total_supply * 0.10)  # 10% for staking rewards
        self.treasury = int(total_supply * 0.05)  # 5% for treasury
        self.circulating_supply = self.current_supply - self.staking_rewards_pool - self.treasury
        self.inflation_rate = 0.02  # 2% annual inflation
    
    def mint_tokens(self, amount: int, purpose: str = 'general') -> bool:
        """
        Mint new tokens.
        
        Args:
            amount: Number of tokens to mint
            purpose: Purpose of the minting
        
        Returns:
            True if successful, False otherwise
        """
        if amount <= 0:
            return False
            
        self.total_supply += amount
        self.current_supply += amount
        
        if purpose == 'staking_rewards':
            self.staking_rewards_pool += amount
        elif purpose == 'treasury':
            self.treasury += amount
        else:
            self.circulating_supply += amount
            
        return True
    
    def burn_tokens(self, amount: int) -> bool:
        """
        Burn tokens to reduce supply.
        
        Args:
            amount: Number of tokens to burn
        
        Returns:
            True if successful, False otherwise
        """
        if amount <= 0 or amount > self.current_supply:
            return False
            
        self.total_supply -= amount
        self.current_supply -= amount
        
        # Burn from circulating supply first
        if amount <= self.circulating_supply:
            self.circulating_supply -= amount
        else:
            remaining = amount - self.circulating_supply
            self.circulating_supply = 0
            self.staking_rewards_pool -= remaining
            
        return True
    
    def get_supply_distribution(self) -> Dict[str, int]:
        """
        Get token supply distribution.
        
        Returns:
            Dictionary with supply distribution details
        """
        return {
            'total': self.total_supply,
            'current': self.current_supply,
            'circulating': self.circulating_supply,
            'staking_rewards': self.staking_rewards_pool,
            'treasury': self.treasury
        }
    
    def calculate_inflation(self, years: int = 1) -> int:
        """
        Calculate inflation over a period of years.
        
        Args:
            years: Number of years
        
        Returns:
            Inflation amount
        """
        inflation = int(self.total_supply * (self.inflation_rate * years))
        return inflation
    
    def get_tokenomics_info(self) -> Dict[str, Any]:
        """
        Get comprehensive tokenomics information.
        
        Returns:
            Dictionary with tokenomics details
        """
        return {
            'supply': self.get_supply_distribution(),
            'inflation_rate': self.inflation_rate,
            'next_year_inflation': self.calculate_inflation(1)
        }
    
    def __repr__(self):
        return f"Tokenomics(total_supply={self.total_supply:,})"
    
    def __str__(self):
        info = self.get_tokenomics_info()
        return (
            f"Tokenomics:\n"
            f"  Total Supply: {info['supply']['total']:,}\n"
            f"  Current Supply: {info['supply']['current']:,}\n"
            f"  Circulating Supply: {info['supply']['circulating']:,}\n"
            f"  Staking Rewards Pool: {info['supply']['staking_rewards']:,}\n"
            f"  Treasury: {info['supply']['treasury']:,}\n"
            f"  Inflation Rate: {info['inflation_rate']:.1%}\n"
            f"  Next Year Inflation: {info['next_year_inflation']:,}"
        )
