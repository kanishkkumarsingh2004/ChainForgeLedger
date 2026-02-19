"""
ChainForgeLedger Stablecoin Framework

Implements algorithmic stablecoin functionality with collateralization and pegging mechanisms.
"""

import time
from typing import Dict, List


class Stablecoin:
    """
    Algorithmic stablecoin implementation with collateralization and pegging.
    
    Attributes:
        name: Stablecoin name
        symbol: Stablecoin symbol
        peg_currency: Currency the stablecoin is pegged to
        target_price: Target price in terms of peg currency
        collateral_ratio: Target collateral ratio (e.g., 1.5 = 150% collateralized)
        collateral_tokens: Accepted collateral tokens
        total_supply: Total stablecoin supply
        circulating_supply: Circulating stablecoin supply
        collateral_reserves: Collateral reserves by token type
        minting_fee: Fee for minting stablecoins
        redemption_fee: Fee for redeeming stablecoins
        price_oracle: Price oracle for pegging
        minting_history: History of minting events
        redemption_history: History of redemption events
        collateral_history: Collateral balance history
    """
    
    def __init__(self, name: str, symbol: str, peg_currency: str,
                 target_price: float = 1.0, collateral_ratio: float = 1.5,
                 minting_fee: float = 0.01, redemption_fee: float = 0.01):
        """
        Initialize a Stablecoin instance.
        
        Args:
            name: Stablecoin name
            symbol: Stablecoin symbol
            peg_currency: Currency to peg against
            target_price: Target price
            collateral_ratio: Target collateral ratio
            minting_fee: Minting fee percentage
            redemption_fee: Redemption fee percentage
        """
        self.name = name
        self.symbol = symbol
        self.peg_currency = peg_currency
        self.target_price = target_price
        self.collateral_ratio = collateral_ratio
        self.minting_fee = minting_fee
        self.redemption_fee = redemption_fee
        self.total_supply = 0
        self.circulating_supply = 0
        self.collateral_reserves: Dict[str, int] = {}
        self.collateral_tokens: List[str] = []
        self.price_oracle = None
        self.minting_history: List[Dict] = []
        self.redemption_history: List[Dict] = []
        self.collateral_history: List[Dict] = []
        self.token_id = self._generate_token_id()
        
    def _generate_token_id(self) -> str:
        """Generate unique token identifier."""
        from chainforgeledger.crypto.hashing import sha256_hash
        data = f"{self.name}:{self.symbol}:{self.peg_currency}:{self.target_price}"
        return sha256_hash(data)
    
    def set_price_oracle(self, oracle):
        """
        Set price oracle for stablecoin pegging.
        
        Args:
            oracle: Price oracle instance with get_price() method
        """
        self.price_oracle = oracle
    
    def add_collateral_token(self, token: str, max_collateral_ratio: float = 0.5):
        """
        Add a collateral token type.
        
        Args:
            token: Token type to accept as collateral
            max_collateral_ratio: Maximum percentage of this token in reserves
        """
        if token not in self.collateral_tokens:
            self.collateral_tokens.append(token)
            self.collateral_reserves[token] = 0
    
    def get_current_price(self) -> float:
        """
        Get current stablecoin price.
        
        Returns:
            Current price in terms of peg currency
        """
        if self.price_oracle:
            return self.price_oracle.get_price()
            
        # Default to target price if no oracle
        return self.target_price
    
    def get_collateral_value(self) -> float:
        """
        Get total collateral value in peg currency.
        
        Returns:
            Total collateral value
        """
        total_value = 0
        
        for token, amount in self.collateral_reserves.items():
            if self.price_oracle:
                price = self.price_oracle.get_price(token)
            else:
                price = 1.0  # Default price
            
            total_value += amount * price
            
        return total_value
    
    def get_collateral_ratio(self) -> float:
        """
        Get current collateral ratio.
        
        Returns:
            Collateral ratio (collateral value / stablecoin supply)
        """
        if self.total_supply == 0:
            return 0.0
            
        return self.get_collateral_value() / (self.total_supply * self.target_price)
    
    def get_reserve_composition(self) -> Dict:
        """
        Get collateral reserve composition.
        
        Returns:
            Reserve composition by token type
        """
        total_value = self.get_collateral_value()
        composition = {}
        
        for token, amount in self.collateral_reserves.items():
            if self.price_oracle:
                price = self.price_oracle.get_price(token)
            else:
                price = 1.0
                
            token_value = amount * price
            composition[token] = token_value / total_value if total_value > 0 else 0
            
        return composition
    
    def mint(self, minter_address: str, amount: int, 
             collateral_token: str, collateral_amount: int) -> bool:
        """
        Mint stablecoins by depositing collateral.
        
        Args:
            minter_address: Minter address
            amount: Amount of stablecoins to mint
            collateral_token: Collateral token type
            collateral_amount: Collateral amount
            
        Returns:
            True if minting was successful
        """
        if amount <= 0 or collateral_amount <= 0:
            return False
            
        if collateral_token not in self.collateral_tokens:
            return False
            
        # Calculate required collateral based on current price and ratio
        required_collateral_value = amount * self.target_price * self.collateral_ratio
        
        if self.price_oracle:
            collateral_price = self.price_oracle.get_price(collateral_token)
        else:
            collateral_price = 1.0
            
        required_collateral_amount = required_collateral_value / collateral_price
        
        if collateral_amount < required_collateral_amount:
            return False
            
        # Calculate minting fee
        minting_fee = int(amount * self.minting_fee)
        
        # Mint stablecoins
        self.total_supply += amount
        self.circulating_supply += amount
        self.collateral_reserves[collateral_token] += collateral_amount
        
        # Record minting event
        self.minting_history.append({
            'minter_address': minter_address,
            'amount': amount,
            'collateral_token': collateral_token,
            'collateral_amount': collateral_amount,
            'minting_fee': minting_fee,
            'timestamp': time.time(),
            'price': self.get_current_price()
        })
        
        self._record_collateral_snapshot()
        
        return True
    
    def redeem(self, redeemer_address: str, amount: int, 
              collateral_token: str) -> int:
        """
        Redeem stablecoins for collateral.
        
        Args:
            redeemer_address: Redeemer address
            amount: Amount of stablecoins to redeem
            collateral_token: Collateral token to receive
            
        Returns:
            Amount of collateral received
        """
        if amount <= 0:
            return 0
            
        if collateral_token not in self.collateral_tokens:
            return 0
            
        if amount > self.circulating_supply:
            return 0
            
        # Calculate redemption fee
        redemption_fee = int(amount * self.redemption_fee)
        net_amount = amount - redemption_fee
        
        # Calculate collateral to return based on current collateral ratio
        collateral_value = net_amount * self.target_price
        
        if self.price_oracle:
            collateral_price = self.price_oracle.get_price(collateral_token)
        else:
            collateral_price = 1.0
            
        collateral_amount = int(collateral_value / collateral_price)
        
        # Check if we have enough collateral
        if self.collateral_reserves.get(collateral_token, 0) < collateral_amount:
            return 0
            
        # Redeem stablecoins
        self.total_supply -= amount
        self.circulating_supply -= amount
        self.collateral_reserves[collateral_token] -= collateral_amount
        
        # Record redemption event
        self.redemption_history.append({
            'redeemer_address': redeemer_address,
            'amount': amount,
            'collateral_token': collateral_token,
            'collateral_amount': collateral_amount,
            'redemption_fee': redemption_fee,
            'timestamp': time.time(),
            'price': self.get_current_price()
        })
        
        self._record_collateral_snapshot()
        
        return collateral_amount
    
    def stabilize_price(self):
        """
        Stabilize price by adjusting supply based on market conditions.
        
        This would implement algorithmic mechanisms like seigniorage shares
        or other stabilization techniques.
        """
        current_price = self.get_current_price()
        
        # If price is above target, we could mint new supply to reduce price
        if current_price > self.target_price * 1.02:
            self._mint_for_stabilization()
            
        # If price is below target, we could burn supply to increase price
        elif current_price < self.target_price * 0.98:
            self._burn_for_stabilization()
    
    def _mint_for_stabilization(self):
        """Internal method for stabilization minting."""
        # This would implement more complex stabilization logic
        adjustment_amount = int(self.total_supply * 0.01)
        self.total_supply += adjustment_amount
        self.circulating_supply += adjustment_amount
    
    def _burn_for_stabilization(self):
        """Internal method for stabilization burning."""
        # This would implement more complex stabilization logic
        adjustment_amount = int(self.total_supply * 0.01)
        self.total_supply -= adjustment_amount
        self.circulating_supply -= adjustment_amount
    
    def _record_collateral_snapshot(self):
        """Record collateral balance snapshot for historical analysis."""
        snapshot = {
            'timestamp': time.time(),
            'total_supply': self.total_supply,
            'circulating_supply': self.circulating_supply,
            'collateral_reserves': self.collateral_reserves.copy(),
            'collateral_ratio': self.get_collateral_ratio(),
            'price': self.get_current_price()
        }
        
        self.collateral_history.append(snapshot)
    
    def get_stablecoin_info(self) -> Dict:
        """
        Get stablecoin information.
        
        Returns:
            Stablecoin information dictionary
        """
        current_price = self.get_current_price()
        collateral_value = self.get_collateral_value()
        collateral_ratio = self.get_collateral_ratio()
        
        return {
            'name': self.name,
            'symbol': self.symbol,
            'peg_currency': self.peg_currency,
            'target_price': self.target_price,
            'current_price': current_price,
            'price_deviation': abs(current_price - self.target_price) / self.target_price * 100,
            'total_supply': self.total_supply,
            'circulating_supply': self.circulating_supply,
            'collateral_value': collateral_value,
            'collateral_ratio': collateral_ratio,
            'minting_fee': self.minting_fee,
            'redemption_fee': self.redemption_fee,
            'collateral_tokens': self.collateral_tokens,
            'reserve_composition': self.get_reserve_composition()
        }
    
    def get_market_stats(self) -> Dict:
        """
        Get market statistics.
        
        Returns:
            Market statistics dictionary
        """
        minting_volume = sum(tx['amount'] for tx in self.minting_history)
        redemption_volume = sum(tx['amount'] for tx in self.redemption_history)
        
        total_fees = sum(tx['minting_fee'] for tx in self.minting_history) + \
                    sum(tx['redemption_fee'] for tx in self.redemption_history)
        
        avg_minting_amount = minting_volume / len(self.minting_history) if self.minting_history else 0
        avg_redemption_amount = redemption_volume / len(self.redemption_history) if self.redemption_history else 0
        
        return {
            'minting_count': len(self.minting_history),
            'minting_volume': minting_volume,
            'avg_minting_amount': avg_minting_amount,
            'redemption_count': len(self.redemption_history),
            'redemption_volume': redemption_volume,
            'avg_redemption_amount': avg_redemption_amount,
            'total_fees': total_fees
        }
    
    def get_collateral_history(self, days: int = 30) -> List[Dict]:
        """
        Get collateral history for the last N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            Collateral history data
        """
        history = []
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for snapshot in self.collateral_history:
            if snapshot['timestamp'] >= cutoff_time:
                history.append(snapshot)
                
        return history
    
    def set_target_price(self, price: float):
        """
        Set target price.
        
        Args:
            price: New target price
            
        Raises:
            Exception: If price is invalid
        """
        if price <= 0:
            raise Exception("Target price must be positive")
            
        self.target_price = price
    
    def set_collateral_ratio(self, ratio: float):
        """
        Set collateral ratio.
        
        Args:
            ratio: New collateral ratio
            
        Raises:
            Exception: If ratio is invalid
        """
        if ratio < 1.0:
            raise Exception("Collateral ratio must be at least 1.0")
            
        self.collateral_ratio = ratio
    
    def set_minting_fee(self, fee: float):
        """
        Set minting fee percentage.
        
        Args:
            fee: New fee percentage
            
        Raises:
            Exception: If fee is invalid
        """
        if fee < 0 or fee > 0.1:
            raise Exception("Minting fee must be between 0 and 10%")
            
        self.minting_fee = fee
    
    def set_redemption_fee(self, fee: float):
        """
        Set redemption fee percentage.
        
        Args:
            fee: New fee percentage
            
        Raises:
            Exception: If fee is invalid
        """
        if fee < 0 or fee > 0.1:
            raise Exception("Redemption fee must be between 0 and 10%")
            
        self.redemption_fee = fee
    
    def __repr__(self):
        """String representation of the Stablecoin."""
        info = self.get_stablecoin_info()
        return (f"{self.symbol} Stablecoin({self.name}, "
                f"Price: {info['current_price']:.2f}, "
                f"Collateral Ratio: {info['collateral_ratio']:.1f}x)")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_stablecoin_info()
        stats = self.get_market_stats()
        
        composition_str = "\n".join([
            f"  {token}: {percent:.1%}" 
            for token, percent in info['reserve_composition'].items()
        ])
        
        return (
            f"{self.name} ({self.symbol})\n"
            f"===================\n"
            f"Peg Currency: {self.peg_currency}\n"
            f"Target Price: {self.target_price}\n"
            f"Current Price: {info['current_price']:.4f} ({info['price_deviation']:.1%} deviation)\n"
            f"Collateral Ratio: {info['collateral_ratio']:.2f}x\n"
            f"Total Supply: {self.total_supply:,}\n"
            f"Circulating Supply: {self.circulating_supply:,}\n"
            f"Collateral Value: {info['collateral_value']:.2f}\n"
            f"\nReserve Composition:\n"
            f"{composition_str}\n"
            f"\nMarket Statistics:\n"
            f"Total Minted: {stats['minting_volume']:,} ({stats['minting_count']} transactions)\n"
            f"Total Redeemed: {stats['redemption_volume']:,} ({stats['redemption_count']} transactions)\n"
            f"Total Fees: {stats['total_fees']:.2f}"
        )


class PriceOracle:
    """
    Simple price oracle implementation for stablecoin pegging.
    """
    
    def __init__(self, base_currency: str):
        """
        Initialize a PriceOracle instance.
        
        Args:
            base_currency: Base currency for pricing
        """
        self.base_currency = base_currency
        self.prices: Dict[str, float] = {}
        self.last_update = 0
    
    def set_price(self, token: str, price: float):
        """
        Set token price.
        
        Args:
            token: Token type
            price: Price in base currency
        """
        if price <= 0:
            raise Exception("Price must be positive")
            
        self.prices[token] = price
        self.last_update = time.time()
    
    def get_price(self, token: str = None) -> float:
        """
        Get token price.
        
        Args:
            token: Token type (defaults to base currency)
            
        Returns:
            Price in base currency
        """
        if token is None:
            return 1.0
            
        return self.prices.get(token, 1.0)
    
    def update_prices(self, new_prices: Dict[str, float]):
        """
        Update multiple token prices.
        
        Args:
            new_prices: Dictionary of token prices
        """
        for token, price in new_prices.items():
            if price <= 0:
                continue
                
            self.prices[token] = price
            
        self.last_update = time.time()
    
    def get_last_update(self) -> float:
        """
        Get last update time.
        
        Returns:
            Last update time in timestamp
        """
        return self.last_update
