"""
ChainForgeLedger Liquidity Pool Engine

Implements automated market maker (AMM) and liquidity pool functionality.
"""

import time
import math
from typing import Dict, List, Optional
from chainforgeledger.crypto.hashing import sha256_hash


class LiquidityPool:
    """
    Liquidity pool implementation for decentralized exchange functionality.
    
    Attributes:
        pool_id: Unique pool identifier
        token_a: First token type in pool
        token_b: Second token type in pool
        reserves_a: Reserve of token A
        reserves_b: Reserve of token B
        total_shares: Total liquidity provider shares
        lp_shares: Liquidity provider shares per address
        fee_percent: Trading fee percentage
        min_liquidity: Minimum liquidity required for pool operation
        swap_fees: Accumulated swap fees
        pool_history: Pool transaction history
    """
    
    def __init__(self, token_a: str, token_b: str,
                 fee_percent: float = 0.3,
                 min_liquidity: int = 100):
        """
        Initialize a LiquidityPool instance.
        
        Args:
            token_a: First token type
            token_b: Second token type
            fee_percent: Trading fee percentage
            min_liquidity: Minimum liquidity required
        """
        self.pool_id = self._generate_pool_id(token_a, token_b)
        self.token_a = token_a
        self.token_b = token_b
        self.reserves_a = 0
        self.reserves_b = 0
        self.total_shares = 0
        self.lp_shares: Dict[str, int] = {}
        self.fee_percent = fee_percent
        self.min_liquidity = min_liquidity
        self.swap_fees = {'token_a': 0, 'token_b': 0}
        self.pool_history: List[Dict] = []
    
    def _generate_pool_id(self, token_a: str, token_b: str) -> str:
        """Generate unique pool identifier."""
        sorted_tokens = sorted([token_a, token_b])
        return sha256_hash(f"{sorted_tokens[0]}:{sorted_tokens[1]}")[:16]
    
    def add_liquidity(self, lp_address: str, amount_a: int, amount_b: int) -> int:
        """
        Add liquidity to the pool.
        
        Args:
            lp_address: Liquidity provider address
            amount_a: Amount of token A to add
            amount_b: Amount of token B to add
            
        Returns:
            Number of liquidity provider shares received
            
        Raises:
            Exception: If liquidity addition fails
        """
        if amount_a <= 0 or amount_b <= 0:
            raise Exception("Amounts must be positive")
            
        # Check price ratio
        if self.reserves_a > 0 and self.reserves_b > 0:
            expected_b = amount_a * (self.reserves_b / self.reserves_a)
            if not math.isclose(amount_b, expected_b, rel_tol=0.01):
                raise Exception("Invalid price ratio")
                
        # Calculate shares
        if self.total_shares == 0:
            shares = int(math.sqrt(amount_a * amount_b))
        else:
            shares = min(
                int(amount_a * self.total_shares / self.reserves_a),
                int(amount_b * self.total_shares / self.reserves_b)
            )
            
        # Add to reserves
        self.reserves_a += amount_a
        self.reserves_b += amount_b
        self.total_shares += shares
        
        # Add to liquidity provider shares
        if lp_address not in self.lp_shares:
            self.lp_shares[lp_address] = 0
        self.lp_shares[lp_address] += shares
        
        # Record transaction
        self.pool_history.append({
            'type': 'add_liquidity',
            'lp_address': lp_address,
            'amount_a': amount_a,
            'amount_b': amount_b,
            'shares_added': shares,
            'timestamp': time.time()
        })
        
        return shares
    
    def remove_liquidity(self, lp_address: str, shares: int) -> Dict:
        """
        Remove liquidity from the pool.
        
        Args:
            lp_address: Liquidity provider address
            shares: Number of shares to remove
            
        Returns:
            Dictionary with withdrawn amounts
            
        Raises:
            Exception: If liquidity removal fails
        """
        if lp_address not in self.lp_shares or self.lp_shares[lp_address] < shares:
            raise Exception("Insufficient shares")
            
        # Calculate withdrawal amounts
        share_ratio = shares / self.total_shares
        amount_a = int(share_ratio * self.reserves_a)
        amount_b = int(share_ratio * self.reserves_b)
        
        # Remove from reserves and shares
        self.reserves_a -= amount_a
        self.reserves_b -= amount_b
        self.total_shares -= shares
        self.lp_shares[lp_address] -= shares
        
        if self.lp_shares[lp_address] == 0:
            del self.lp_shares[lp_address]
            
        # Record transaction
        self.pool_history.append({
            'type': 'remove_liquidity',
            'lp_address': lp_address,
            'amount_a': amount_a,
            'amount_b': amount_b,
            'shares_removed': shares,
            'timestamp': time.time()
        })
        
        return {'token_a': amount_a, 'token_b': amount_b}
    
    def swap(self, from_token: str, to_token: str, 
            from_amount: int, trader_address: str) -> int:
        """
        Swap tokens using the pool.
        
        Args:
            from_token: Token to swap from
            to_token: Token to swap to
            from_amount: Amount to swap
            trader_address: Trader address
            
        Returns:
            Amount of to_token received
            
        Raises:
            Exception: If swap fails
        """
        if from_token == to_token:
            raise Exception("Cannot swap identical tokens")
            
        if from_amount <= 0:
            raise Exception("Amount must be positive")
            
        # Check token validity
        if from_token not in [self.token_a, self.token_b] or to_token not in [self.token_a, self.token_b]:
            raise Exception("Invalid token type")
            
        # Calculate fee
        fee = int(from_amount * self.fee_percent / 100)
        amount_after_fee = from_amount - fee
        
        # Calculate output using constant product formula
        if from_token == self.token_a and to_token == self.token_b:
            input_reserve = self.reserves_a
            output_reserve = self.reserves_b
            
            output_amount = int(
                (amount_after_fee * output_reserve) / (input_reserve + amount_after_fee)
            )
            
            if self.reserves_b < output_amount:
                raise Exception("Insufficient liquidity")
                
            self.reserves_a += from_amount
            self.reserves_b -= output_amount
            self.swap_fees['token_a'] += fee
            
        elif from_token == self.token_b and to_token == self.token_a:
            input_reserve = self.reserves_b
            output_reserve = self.reserves_a
            
            output_amount = int(
                (amount_after_fee * output_reserve) / (input_reserve + amount_after_fee)
            )
            
            if self.reserves_a < output_amount:
                raise Exception("Insufficient liquidity")
                
            self.reserves_b += from_amount
            self.reserves_a -= output_amount
            self.swap_fees['token_b'] += fee
            
        else:
            raise Exception("Unsupported token pair")
            
        # Record transaction
        self.pool_history.append({
            'type': 'swap',
            'trader_address': trader_address,
            'from_token': from_token,
            'to_token': to_token,
            'from_amount': from_amount,
            'to_amount': output_amount,
            'fee': fee,
            'timestamp': time.time()
        })
        
        return output_amount
    
    def get_price(self, token_in: str, token_out: str) -> float:
        """
        Get current price for token swap.
        
        Args:
            token_in: Token being swapped in
            token_out: Token being swapped out
            
        Returns:
            Price of token_out in terms of token_in
            
        Raises:
            Exception: If token pair is invalid
        """
        if token_in not in [self.token_a, self.token_b] or token_out not in [self.token_a, self.token_b]:
            raise Exception("Invalid token type")
            
        if token_in == self.token_a and token_out == self.token_b:
            if self.reserves_a == 0:
                return 0.0
            return self.reserves_b / self.reserves_a
            
        elif token_in == self.token_b and token_out == self.token_a:
            if self.reserves_b == 0:
                return 0.0
            return self.reserves_a / self.reserves_b
            
        else:
            raise Exception("Unsupported token pair")
    
    def get_pool_info(self) -> Dict:
        """
        Get pool information.
        
        Returns:
            Pool information dictionary
        """
        tvl = self.reserves_a + self.reserves_b
        fee_apr = self._calculate_fee_apr()
        
        return {
            'pool_id': self.pool_id,
            'token_a': self.token_a,
            'token_b': self.token_b,
            'reserves_a': self.reserves_a,
            'reserves_b': self.reserves_b,
            'total_shares': self.total_shares,
            'fee_percent': self.fee_percent,
            'liquidity_providers': len(self.lp_shares),
            'total_value_locked': tvl,
            'swap_fees': self.swap_fees,
            'fee_apr': fee_apr,
            'price_ratio': self.get_price(self.token_a, self.token_b)
        }
    
    def _calculate_fee_apr(self) -> float:
        """Calculate annual fee APR."""
        if self.reserves_a == 0 or self.reserves_b == 0:
            return 0.0
            
        # This would require historical fee data
        return 0.0
    
    def get_lp_share(self, lp_address: str) -> int:
        """
        Get liquidity provider share.
        
        Args:
            lp_address: Liquidity provider address
            
        Returns:
            Number of shares held
        """
        return self.lp_shares.get(lp_address, 0)
    
    def get_lp_info(self, lp_address: str) -> Dict:
        """
        Get liquidity provider information.
        
        Args:
            lp_address: Liquidity provider address
            
        Returns:
            LP information dictionary
        """
        shares = self.get_lp_share(lp_address)
        
        if shares == 0:
            return {
                'lp_address': lp_address,
                'shares': 0,
                'share_percentage': 0.0,
                'token_a_amount': 0,
                'token_b_amount': 0,
                'pool_info': self.get_pool_info()
            }
            
        share_ratio = shares / self.total_shares
        token_a_amount = int(share_ratio * self.reserves_a)
        token_b_amount = int(share_ratio * self.reserves_b)
        
        return {
            'lp_address': lp_address,
            'shares': shares,
            'share_percentage': share_ratio * 100,
            'token_a_amount': token_a_amount,
            'token_b_amount': token_b_amount,
            'pool_info': self.get_pool_info()
        }
    
    def get_all_lps(self) -> List[Dict]:
        """
        Get all liquidity providers.
        
        Returns:
            List of LP information dictionaries
        """
        lps = []
        for lp_address in self.lp_shares:
            lps.append(self.get_lp_info(lp_address))
            
        # Sort by shares (descending)
        return sorted(lps, key=lambda x: x['shares'], reverse=True)
    
    def get_transaction_history(self, limit: int = 100) -> List[Dict]:
        """
        Get pool transaction history.
        
        Args:
            limit: Number of transactions to return
            
        Returns:
            List of pool transactions
        """
        return self.pool_history[-limit:][::-1]
    
    def get_pool_stats(self) -> Dict:
        """
        Get pool statistics.
        
        Returns:
            Pool statistics dictionary
        """
        transactions = self.get_transaction_history()
        swaps = [tx for tx in transactions if tx['type'] == 'swap']
        liquidity_additions = [tx for tx in transactions if tx['type'] == 'add_liquidity']
        liquidity_removals = [tx for tx in transactions if tx['type'] == 'remove_liquidity']
        
        total_volume = sum(tx['from_amount'] for tx in swaps)
        avg_swap_size = total_volume / len(swaps) if swaps else 0
        
        return {
            'total_transactions': len(transactions),
            'swaps': len(swaps),
            'liquidity_additions': len(liquidity_additions),
            'liquidity_removals': len(liquidity_removals),
            'total_volume': total_volume,
            'avg_swap_size': avg_swap_size,
            'total_fees': sum(tx['fee'] for tx in swaps),
            'tvl': self.get_pool_info()['total_value_locked']
        }
    
    def set_fee_percent(self, fee_percent: float):
        """
        Set trading fee percentage.
        
        Args:
            fee_percent: Trading fee percentage (0.0 to 10.0)
            
        Raises:
            Exception: If fee is invalid
        """
        if fee_percent < 0 or fee_percent > 10:
            raise Exception("Fee percentage must be between 0 and 10")
            
        self.fee_percent = fee_percent
    
    def __repr__(self):
        """String representation of the LiquidityPool."""
        info = self.get_pool_info()
        return (f"LiquidityPool({self.token_a}/{self.token_b}, "
                f"TVL={info['total_value_locked']}, "
                f"LPs={info['liquidity_providers']})")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_pool_info()
        stats = self.get_pool_stats()
        
        return (
            f"Liquidity Pool {self.pool_id}\n"
            f"====================\n"
            f"Token Pair: {self.token_a}/{self.token_b}\n"
            f"Reserves: {info['reserves_a']} {self.token_a}, {info['reserves_b']} {self.token_b}\n"
            f"Total Value Locked: {info['total_value_locked']}\n"
            f"Fee Percentage: {info['fee_percent']}%\n"
            f"Liquidity Providers: {info['liquidity_providers']}\n"
            f"Total Shares: {info['total_shares']}\n"
            f"Price Ratio: {info['price_ratio']:.4f}\n"
            f"\nStatistics:\n"
            f"Total Transactions: {stats['total_transactions']}\n"
            f"Total Volume: {stats['total_volume']}\n"
            f"Total Fees: {stats['total_fees']}\n"
            f"Average Swap Size: {stats['avg_swap_size']:.2f}\n"
            f"TVL: {stats['tvl']}"
        )


class LiquidityPoolManager:
    """
    Manager for multiple liquidity pools.
    """
    
    def __init__(self):
        """Initialize a LiquidityPoolManager instance."""
        self.pools: Dict[str, LiquidityPool] = {}
        self.pool_stats: Dict[str, Dict] = {}
    
    def create_pool(self, token_a: str, token_b: str, 
                   fee_percent: float = 0.3,
                   min_liquidity: int = 100) -> LiquidityPool:
        """
        Create a new liquidity pool.
        
        Args:
            token_a: First token type
            token_b: Second token type
            fee_percent: Trading fee percentage
            min_liquidity: Minimum liquidity required
            
        Returns:
            Created liquidity pool instance
        """
        pool = LiquidityPool(token_a, token_b, fee_percent, min_liquidity)
        self.pools[pool.pool_id] = pool
        return pool
    
    def get_pool(self, pool_id: str) -> Optional[LiquidityPool]:
        """
        Get pool by ID.
        
        Args:
            pool_id: Pool identifier
            
        Returns:
            Pool instance if found, None otherwise
        """
        return self.pools.get(pool_id)
    
    def get_pool_by_tokens(self, token_a: str, token_b: str) -> Optional[LiquidityPool]:
        """
        Get pool by token pair.
        
        Args:
            token_a: First token type
            token_b: Second token type
            
        Returns:
            Pool instance if found, None otherwise
        """
        sorted_tokens = sorted([token_a, token_b])
        target_key = f"{sorted_tokens[0]}:{sorted_tokens[1]}"
        
        for pool in self.pools.values():
            pool_tokens = sorted([pool.token_a, pool.token_b])
            pool_key = f"{pool_tokens[0]}:{pool_tokens[1]}"
            
            if pool_key == target_key:
                return pool
                
        return None
    
    def get_all_pools(self) -> List[LiquidityPool]:
        """
        Get all pools.
        
        Returns:
            List of all pool instances
        """
        return list(self.pools.values())
    
    def get_total_tvl(self) -> int:
        """
        Get total TVL across all pools.
        
        Returns:
            Total TVL
        """
        return sum(pool.get_pool_info()['total_value_locked'] for pool in self.pools.values())
    
    def get_total_fees(self) -> int:
        """
        Get total fees across all pools.
        
        Returns:
            Total fees
        """
        return sum(pool.swap_fees['token_a'] + pool.swap_fees['token_b'] for pool in self.pools.values())
    
    def get_system_stats(self) -> Dict:
        """
        Get system-wide liquidity pool statistics.
        
        Returns:
            System statistics dictionary
        """
        pool_count = len(self.pools)
        total_tvl = self.get_total_tvl()
        total_fees = self.get_total_fees()
        total_liquidity_providers = sum(len(pool.lp_shares) for pool in self.pools.values())
        
        return {
            'pool_count': pool_count,
            'total_tvl': total_tvl,
            'total_fees': total_fees,
            'total_liquidity_providers': total_liquidity_providers,
            'avg_tvl_per_pool': total_tvl / pool_count if pool_count > 0 else 0
        }
    
    def __repr__(self):
        """String representation of the LiquidityPoolManager."""
        stats = self.get_system_stats()
        return (f"LiquidityPoolManager(pools={stats['pool_count']}, "
                f"TVL={stats['total_tvl']}, "
                f"LPs={stats['total_liquidity_providers']})")
