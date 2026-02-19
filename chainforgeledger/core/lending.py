"""
ChainForgeLedger Lending & Borrowing Module

Implements decentralized lending and borrowing functionality.
"""

import time
from typing import Dict, List, Optional
from chainforgeledger.crypto.hashing import sha256_hash


class LendingPool:
    """
    Lending pool implementation for decentralized lending and borrowing.
    
    Attributes:
        pool_id: Unique pool identifier
        token: Token used in the pool
        total_deposits: Total amount of tokens deposited
        total_borrowed: Total amount of tokens borrowed
        interest_rate: Current interest rate (APY)
        collateral_ratio: Minimum collateral ratio required for borrowing
        liquidation_threshold: Collateral ratio below which positions are liquidated
        liquidation_bonus: Bonus for liquidators
        borrowers: Dictionary of borrower positions
        lenders: Dictionary of lender deposits
        pool_history: Pool transaction history
        last_interest_update: Last time interest was calculated
    """
    
    def __init__(self, token: str,
                 interest_rate: float = 0.1,
                 collateral_ratio: float = 1.5,
                 liquidation_threshold: float = 1.25,
                 liquidation_bonus: float = 0.05):
        """
        Initialize a LendingPool instance.
        
        Args:
            token: Token type for the pool
            interest_rate: Base interest rate (APY)
            collateral_ratio: Minimum collateral ratio (e.g., 1.5 = 150%)
            liquidation_threshold: Liquidation threshold (e.g., 1.25 = 125%)
            liquidation_bonus: Liquidation bonus percentage (e.g., 0.05 = 5%)
        """
        self.pool_id = self._generate_pool_id(token)
        self.token = token
        self.total_deposits = 0
        self.total_borrowed = 0
        self.interest_rate = interest_rate
        self.collateral_ratio = collateral_ratio
        self.liquidation_threshold = liquidation_threshold
        self.liquidation_bonus = liquidation_bonus
        self.borrowers: Dict[str, Dict] = {}
        self.lenders: Dict[str, Dict] = {}
        self.pool_history: List[Dict] = []
        self.last_interest_update = time.time()
    
    def _generate_pool_id(self, token: str) -> str:
        """Generate unique pool identifier."""
        return sha256_hash(f"lending:{token}:{time.time()}")[:16]
    
    def deposit(self, lender_address: str, amount: int) -> bool:
        """
        Deposit tokens into the lending pool.
        
        Args:
            lender_address: Lender address
            amount: Amount to deposit
            
        Returns:
            True if deposit was successful
        """
        if amount <= 0:
            return False
            
        # Update interest before processing
        self._update_interest()
        
        if lender_address not in self.lenders:
            self.lenders[lender_address] = {
                'principal': 0,
                'interest_earned': 0,
                'last_deposit_time': time.time()
            }
            
        self.lenders[lender_address]['principal'] += amount
        self.total_deposits += amount
        
        # Record transaction
        self.pool_history.append({
            'type': 'deposit',
            'address': lender_address,
            'amount': amount,
            'timestamp': time.time()
        })
        
        return True
    
    def withdraw(self, lender_address: str, amount: int) -> bool:
        """
        Withdraw tokens from the lending pool.
        
        Args:
            lender_address: Lender address
            amount: Amount to withdraw
            
        Returns:
            True if withdrawal was successful
        """
        if amount <= 0:
            return False
            
        # Update interest before processing
        self._update_interest()
        
        if lender_address not in self.lenders:
            return False
            
        available = self.lenders[lender_address]['principal'] + self.lenders[lender_address]['interest_earned']
        
        if available < amount:
            return False
            
        self.lenders[lender_address]['principal'] -= amount
        self.total_deposits -= amount
        
        # Record transaction
        self.pool_history.append({
            'type': 'withdraw',
            'address': lender_address,
            'amount': amount,
            'timestamp': time.time()
        })
        
        return True
    
    def borrow(self, borrower_address: str, amount: int, 
              collateral_address: str, collateral_amount: int) -> bool:
        """
        Borrow tokens from the lending pool.
        
        Args:
            borrower_address: Borrower address
            amount: Amount to borrow
            collateral_address: Collateral token address
            collateral_amount: Collateral amount
            
        Returns:
            True if borrowing was successful
        """
        if amount <= 0 or collateral_amount <= 0:
            return False
            
        # Update interest before processing
        self._update_interest()
        
        # Check if there are available funds
        available_to_borrow = self.total_deposits - self.total_borrowed
        
        if available_to_borrow < amount:
            return False
            
        # Calculate collateral ratio
        collateral_ratio = collateral_amount / amount
        
        if collateral_ratio < self.collateral_ratio:
            return False
            
        if borrower_address not in self.borrowers:
            self.borrowers[borrower_address] = {
                'principal': 0,
                'interest_owed': 0,
                'collateral': {
                    'token': collateral_address,
                    'amount': 0
                },
                'last_borrow_time': time.time(),
                'liquidation_price': None
            }
            
        self.borrowers[borrower_address]['principal'] += amount
        self.borrowers[borrower_address]['collateral']['token'] = collateral_address
        self.borrowers[borrower_address]['collateral']['amount'] += collateral_amount
        self.total_borrowed += amount
        
        # Calculate liquidation price
        self.borrowers[borrower_address]['liquidation_price'] = \
            collateral_amount / (amount * self.liquidation_threshold)
        
        # Record transaction
        self.pool_history.append({
            'type': 'borrow',
            'address': borrower_address,
            'amount': amount,
            'collateral_amount': collateral_amount,
            'collateral_token': collateral_address,
            'timestamp': time.time()
        })
        
        return True
    
    def repay(self, borrower_address: str, amount: int) -> bool:
        """
        Repay borrowed tokens.
        
        Args:
            borrower_address: Borrower address
            amount: Amount to repay
            
        Returns:
            True if repayment was successful
        """
        if amount <= 0:
            return False
            
        # Update interest before processing
        self._update_interest()
        
        if borrower_address not in self.borrowers or self.borrowers[borrower_address]['principal'] < amount:
            return False
            
        self.borrowers[borrower_address]['principal'] -= amount
        self.total_borrowed -= amount
        
        # Record transaction
        self.pool_history.append({
            'type': 'repay',
            'address': borrower_address,
            'amount': amount,
            'timestamp': time.time()
        })
        
        return True
    
    def liquidate(self, borrower_address: str, liquidator_address: str) -> bool:
        """
        Liquidate a borrower's position.
        
        Args:
            borrower_address: Borrower address to liquidate
            liquidator_address: Liquidator address
            
        Returns:
            True if liquidation was successful
        """
        if borrower_address not in self.borrowers:
            return False
            
        # Calculate current collateral ratio
        current_ratio = self.borrowers[borrower_address]['collateral']['amount'] / \
                       (self.borrowers[borrower_address]['principal'] + self.borrowers[borrower_address]['interest_owed'])
        
        if current_ratio >= self.liquidation_threshold:
            return False
            
        # Calculate liquidation amount
        borrowed_amount = self.borrowers[borrower_address]['principal']
        collateral_amount = self.borrowers[borrower_address]['collateral']['amount']
        liquidation_bonus = collateral_amount * self.liquidation_bonus
        liquidation_amount = collateral_amount + liquidation_bonus
        
        # Transfer collateral to liquidator
        # In a real implementation, this would interact with the token system
        
        # Remove borrower position
        del self.borrowers[borrower_address]
        self.total_borrowed -= borrowed_amount
        
        # Record transaction
        self.pool_history.append({
            'type': 'liquidation',
            'borrower_address': borrower_address,
            'liquidator_address': liquidator_address,
            'collateral_amount': collateral_amount,
            'collateral_token': self.borrowers[borrower_address]['collateral']['token'],
            'timestamp': time.time()
        })
        
        return True
    
    def _update_interest(self):
        """Update interest for all lenders and borrowers."""
        current_time = time.time()
        time_passed = current_time - self.last_interest_update
        
        if time_passed < 3600:  # Update at most once per hour
            return
            
        # Calculate interest per second
        hourly_rate = self.interest_rate / 8760
        per_second_rate = hourly_rate / 3600
        time_factor = time_passed * per_second_rate
        
        # Update lenders' interest
        for lender in self.lenders.values():
            interest = lender['principal'] * time_factor
            lender['interest_earned'] += interest
        
        # Update borrowers' interest
        for borrower in self.borrowers.values():
            interest = borrower['principal'] * time_factor
            borrower['interest_owed'] += interest
        
        self.last_interest_update = current_time
    
    def get_pool_info(self) -> Dict:
        """
        Get pool information.
        
        Returns:
            Pool information dictionary
        """
        utilization_rate = self.total_borrowed / self.total_deposits if self.total_deposits > 0 else 0
        
        return {
            'pool_id': self.pool_id,
            'token': self.token,
            'total_deposits': self.total_deposits,
            'total_borrowed': self.total_borrowed,
            'available_liquidity': self.total_deposits - self.total_borrowed,
            'utilization_rate': utilization_rate,
            'interest_rate': self.interest_rate,
            'collateral_ratio': self.collateral_ratio,
            'liquidation_threshold': self.liquidation_threshold,
            'liquidation_bonus': self.liquidation_bonus,
            'borrowers_count': len(self.borrowers),
            'lenders_count': len(self.lenders)
        }
    
    def get_lender_info(self, lender_address: str) -> Dict:
        """
        Get lender information.
        
        Args:
            lender_address: Lender address
            
        Returns:
            Lender information dictionary
        """
        self._update_interest()
        
        if lender_address not in self.lenders:
            return {
                'address': lender_address,
                'principal': 0,
                'interest_earned': 0,
                'total_balance': 0,
                'pool_info': self.get_pool_info()
            }
            
        return {
            'address': lender_address,
            'principal': self.lenders[lender_address]['principal'],
            'interest_earned': self.lenders[lender_address]['interest_earned'],
            'total_balance': self.lenders[lender_address]['principal'] + self.lenders[lender_address]['interest_earned'],
            'pool_info': self.get_pool_info()
        }
    
    def get_borrower_info(self, borrower_address: str) -> Dict:
        """
        Get borrower information.
        
        Args:
            borrower_address: Borrower address
            
        Returns:
            Borrower information dictionary
        """
        self._update_interest()
        
        if borrower_address not in self.borrowers:
            return {
                'address': borrower_address,
                'principal': 0,
                'interest_owed': 0,
                'collateral': {
                    'token': '',
                    'amount': 0
                },
                'collateral_ratio': 0,
                'liquidation_price': None,
                'pool_info': self.get_pool_info()
            }
            
        collateral_ratio = self.borrowers[borrower_address]['collateral']['amount'] / \
                       (self.borrowers[borrower_address]['principal'] + self.borrowers[borrower_address]['interest_owed'])
        
        return {
            'address': borrower_address,
            'principal': self.borrowers[borrower_address]['principal'],
            'interest_owed': self.borrowers[borrower_address]['interest_owed'],
            'collateral': self.borrowers[borrower_address]['collateral'],
            'collateral_ratio': collateral_ratio,
            'liquidation_price': self.borrowers[borrower_address]['liquidation_price'],
            'pool_info': self.get_pool_info()
        }
    
    def get_all_lenders(self) -> List[Dict]:
        """
        Get all lenders.
        
        Returns:
            List of lender information dictionaries
        """
        lenders = []
        for lender_address in self.lenders:
            lenders.append(self.get_lender_info(lender_address))
            
        return sorted(lenders, key=lambda x: x['total_balance'], reverse=True)
    
    def get_all_borrowers(self) -> List[Dict]:
        """
        Get all borrowers.
        
        Returns:
            List of borrower information dictionaries
        """
        borrowers = []
        for borrower_address in self.borrowers:
            borrowers.append(self.get_borrower_info(borrower_address))
            
        return sorted(borrowers, key=lambda x: x['principal'], reverse=True)
    
    def get_liquidatable_positions(self) -> List[Dict]:
        """
        Get all liquidatable positions.
        
        Returns:
            List of liquidatable positions
        """
        positions = []
        for borrower_address in self.borrowers:
            info = self.get_borrower_info(borrower_address)
            if info['collateral_ratio'] < self.liquidation_threshold:
                positions.append(info)
                
        return sorted(positions, key=lambda x: x['collateral_ratio'])
    
    def get_pool_stats(self) -> Dict:
        """
        Get pool statistics.
        
        Returns:
            Pool statistics dictionary
        """
        transactions = self.pool_history
        deposit_count = len([tx for tx in transactions if tx['type'] == 'deposit'])
        withdraw_count = len([tx for tx in transactions if tx['type'] == 'withdraw'])
        borrow_count = len([tx for tx in transactions if tx['type'] == 'borrow'])
        repay_count = len([tx for tx in transactions if tx['type'] == 'repay'])
        liquidation_count = len([tx for tx in transactions if tx['type'] == 'liquidation'])
        
        total_deposit_amount = sum(tx['amount'] for tx in transactions if tx['type'] == 'deposit')
        total_withdraw_amount = sum(tx['amount'] for tx in transactions if tx['type'] == 'withdraw')
        total_borrow_amount = sum(tx['amount'] for tx in transactions if tx['type'] == 'borrow')
        total_repay_amount = sum(tx['amount'] for tx in transactions if tx['type'] == 'repay')
        
        avg_deposit_size = total_deposit_amount / deposit_count if deposit_count > 0 else 0
        avg_borrow_size = total_borrow_amount / borrow_count if borrow_count > 0 else 0
        
        return {
            'total_transactions': len(transactions),
            'deposit_count': deposit_count,
            'withdraw_count': withdraw_count,
            'borrow_count': borrow_count,
            'repay_count': repay_count,
            'liquidation_count': liquidation_count,
            'total_deposit_amount': total_deposit_amount,
            'total_withdraw_amount': total_withdraw_amount,
            'total_borrow_amount': total_borrow_amount,
            'total_repay_amount': total_repay_amount,
            'avg_deposit_size': avg_deposit_size,
            'avg_borrow_size': avg_borrow_size
        }
    
    def __repr__(self):
        """String representation of the LendingPool."""
        info = self.get_pool_info()
        return (f"LendingPool({self.token}, "
                f"Deposits={info['total_deposits']}, "
                f"Borrowed={info['total_borrowed']}, "
                f"Utilization={info['utilization_rate']:.1%})")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_pool_info()
        stats = self.get_pool_stats()
        
        return (
            f"Lending Pool {self.pool_id}\n"
            f"==================\n"
            f"Token: {self.token}\n"
            f"Deposits: {info['total_deposits']}\n"
            f"Borrowed: {info['total_borrowed']}\n"
            f"Available: {info['available_liquidity']}\n"
            f"Utilization: {info['utilization_rate']:.1%}\n"
            f"Interest Rate: {info['interest_rate']:.1%} APY\n"
            f"Lenders: {info['lenders_count']}\n"
            f"Borrowers: {info['borrowers_count']}\n"
            f"Collateral Ratio: {info['collateral_ratio']:.0f}:1\n"
            f"Liquidation Threshold: {info['liquidation_threshold']:.0f}:1\n"
            f"Liquidation Bonus: {info['liquidation_bonus']:.0%}\n"
            f"\nStatistics:\n"
            f"Total Transactions: {stats['total_transactions']}\n"
            f"Deposits: {stats['deposit_count']} ({stats['total_deposit_amount']})\n"
            f"Borrows: {stats['borrow_count']} ({stats['total_borrow_amount']})\n"
            f"Avg Deposit: {stats['avg_deposit_size']:.2f}\n"
            f"Avg Borrow: {stats['avg_borrow_size']:.2f}"
        )


class LendingPlatform:
    """
    Decentralized lending platform managing multiple lending pools.
    """
    
    def __init__(self):
        """Initialize a LendingPlatform instance."""
        self.pools: Dict[str, LendingPool] = {}
        self.platform_stats: Dict[str, Dict] = {}
    
    def create_pool(self, token: str,
                   interest_rate: float = 0.1,
                   collateral_ratio: float = 1.5,
                   liquidation_threshold: float = 1.25,
                   liquidation_bonus: float = 0.05) -> LendingPool:
        """
        Create a new lending pool.
        
        Args:
            token: Token type for the pool
            interest_rate: Base interest rate (APY)
            collateral_ratio: Minimum collateral ratio
            liquidation_threshold: Liquidation threshold
            liquidation_bonus: Liquidation bonus percentage
            
        Returns:
            Created lending pool instance
        """
        pool = LendingPool(token, interest_rate, collateral_ratio, 
                        liquidation_threshold, liquidation_bonus)
        self.pools[pool.pool_id] = pool
        return pool
    
    def get_pool(self, pool_id: str) -> Optional[LendingPool]:
        """
        Get pool by ID.
        
        Args:
            pool_id: Pool identifier
            
        Returns:
            Pool instance if found, None otherwise
        """
        return self.pools.get(pool_id)
    
    def get_pool_by_token(self, token: str) -> Optional[LendingPool]:
        """
        Get pool by token type.
        
        Args:
            token: Token type
            
        Returns:
            Pool instance if found, None otherwise
        """
        for pool in self.pools.values():
            if pool.token == token:
                return pool
                
        return None
    
    def get_all_pools(self) -> List[LendingPool]:
        """
        Get all pools.
        
        Returns:
            List of all pool instances
        """
        return list(self.pools.values())
    
    def get_total_deposits(self) -> int:
        """
        Get total deposits across all pools.
        
        Returns:
            Total deposits
        """
        return sum(pool.total_deposits for pool in self.pools.values())
    
    def get_total_borrowed(self) -> int:
        """
        Get total borrowed across all pools.
        
        Returns:
            Total borrowed
        """
        return sum(pool.total_borrowed for pool in self.pools.values())
    
    def get_system_stats(self) -> Dict:
        """
        Get system-wide lending statistics.
        
        Returns:
            System statistics dictionary
        """
        pool_count = len(self.pools)
        total_deposits = self.get_total_deposits()
        total_borrowed = self.get_total_borrowed()
        available_liquidity = total_deposits - total_borrowed
        
        total_lenders = sum(len(pool.lenders) for pool in self.pools.values())
        total_borrowers = sum(len(pool.borrowers) for pool in self.pools.values())
        
        utilization_rate = total_borrowed / total_deposits if total_deposits > 0 else 0
        
        return {
            'pool_count': pool_count,
            'total_deposits': total_deposits,
            'total_borrowed': total_borrowed,
            'available_liquidity': available_liquidity,
            'utilization_rate': utilization_rate,
            'total_lenders': total_lenders,
            'total_borrowers': total_borrowers,
            'avg_lenders_per_pool': total_lenders / pool_count if pool_count > 0 else 0,
            'avg_borrowers_per_pool': total_borrowers / pool_count if pool_count > 0 else 0
        }
    
    def __repr__(self):
        """String representation of the LendingPlatform."""
        stats = self.get_system_stats()
        return (f"LendingPlatform(pools={stats['pool_count']}, "
                f"deposits={stats['total_deposits']}, "
                f"borrowed={stats['total_borrowed']}, "
                f"utilization={stats['utilization_rate']:.1%})")
