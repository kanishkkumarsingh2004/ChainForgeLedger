"""
ChainForgeLedger Fee Distribution System

Implements fee distribution to validators, treasury, and other stakeholders.
"""

import time
from typing import Dict, List
from chainforgeledger.tokenomics.treasury import TreasuryManager


class FeeDistributionSystem:
    """
    Fee distribution system for blockchain transaction fees.
    
    Attributes:
        fee_distribution: Fee distribution percentages to different stakeholders
        accumulated_fees: Accumulated fees by category
        distribution_history: History of fee distributions
        validator_rewards: Validator reward information
        treasury_manager: Treasury manager for fee collection
        minimum_distribution_amount: Minimum fee amount to trigger distribution
        distribution_interval: Fee distribution interval
        last_distribution_time: Last fee distribution time
    """
    
    DEFAULT_DISTRIBUTION = {
        'validators': 0.7,    # 70% to validators
        'treasury': 0.2,      # 20% to treasury
        'development': 0.1,   # 10% to development fund
        'community': 0.0      # 0% to community fund (can be activated)
    }
    
    def __init__(self, treasury: TreasuryManager,
                 minimum_distribution_amount: int = 100,
                 distribution_interval: int = 86400):
        """
        Initialize a FeeDistributionSystem instance.
        
        Args:
            treasury: Treasury manager
            minimum_distribution_amount: Minimum fee amount to trigger distribution
            distribution_interval: Fee distribution interval in seconds
        """
        self.fee_distribution = self.DEFAULT_DISTRIBUTION.copy()
        self.accumulated_fees = {category: 0 for category in self.fee_distribution}
        self.distribution_history: List[Dict] = []
        self.validator_rewards: Dict[str, int] = {}
        self.treasury_manager = treasury
        self.minimum_distribution_amount = minimum_distribution_amount
        self.distribution_interval = distribution_interval
        self.last_distribution_time = time.time()
    
    def collect_transaction_fee(self, fee_amount: int,
                               validator_address: str = None) -> bool:
        """
        Collect transaction fee from network.
        
        Args:
            fee_amount: Transaction fee amount
            validator_address: Validator that processed the transaction
            
        Returns:
            True if fee collection was successful
        """
        if fee_amount <= 0:
            return False
            
        # Distribute fee to stakeholders based on percentage
        for category, percentage in self.fee_distribution.items():
            fee_part = int(fee_amount * percentage)
            self.accumulated_fees[category] += fee_part
            
            # Track validator rewards separately for distribution
            if category == 'validators' and validator_address:
                if validator_address not in self.validator_rewards:
                    self.validator_rewards[validator_address] = 0
                self.validator_rewards[validator_address] += fee_part
                
        return True
    
    def distribute_fees(self, force_distribution: bool = False) -> Dict:
        """
        Distribute accumulated fees to stakeholders.
        
        Args:
            force_distribution: Force distribution regardless of minimum amount or interval
            
        Returns:
            Distribution information dictionary
        """
        total_fees = sum(self.accumulated_fees.values())
        
        if not force_distribution:
            if total_fees < self.minimum_distribution_amount:
                return {'success': False, 'reason': 'Insufficient fee amount'}
                
            time_since_distribution = time.time() - self.last_distribution_time
            if time_since_distribution < self.distribution_interval:
                return {'success': False, 'reason': 'Distribution interval not reached'}
                
        # Calculate distribution amounts
        distribution = {
            category: int(fee_amount)
            for category, fee_amount in self.accumulated_fees.items()
        }
        
        # Distribute fees to respective stakeholders
        self._distribute_to_treasury(distribution.get('treasury', 0))
        self._distribute_to_development_fund(distribution.get('development', 0))
        self._distribute_to_community_fund(distribution.get('community', 0))
        self._distribute_to_validators(distribution.get('validators', 0))
        
        # Record distribution
        distribution_record = {
            'timestamp': time.time(),
            'total_amount': total_fees,
            'distribution': distribution,
            'validator_rewards': self.validator_rewards.copy(),
            'method': 'auto' if not force_distribution else 'manual'
        }
        
        self.distribution_history.append(distribution_record)
        
        # Reset accumulated fees
        self.accumulated_fees = {category: 0 for category in self.fee_distribution}
        self.validator_rewards.clear()
        self.last_distribution_time = time.time()
        
        return {
            'success': True,
            'total_amount': total_fees,
            'distribution': distribution,
            'timestamp': distribution_record['timestamp']
        }
    
    def _distribute_to_treasury(self, amount: int):
        """Distribute fees to treasury."""
        if amount > 0:
            self.treasury_manager.add_balance(amount)
    
    def _distribute_to_development_fund(self, amount: int):
        """Distribute fees to development fund."""
        # This would implement development fund logic
    
    def _distribute_to_community_fund(self, amount: int):
        """Distribute fees to community fund."""
        # This would implement community fund logic
    
    def _distribute_to_validators(self, amount: int):
        """Distribute fees to validators based on their contributions."""
        # In a real implementation, this would distribute based on validator performance
        # For now, we'll just track the total validator fees
    
    def get_fee_distribution_info(self) -> Dict:
        """
        Get fee distribution information.
        
        Returns:
            Distribution information dictionary
        """
        total_fees = sum(self.accumulated_fees.values())
        time_since_distribution = time.time() - self.last_distribution_time
        time_remaining = max(0, self.distribution_interval - time_since_distribution)
        
        return {
            'total_fees': total_fees,
            'minimum_distribution_amount': self.minimum_distribution_amount,
            'time_since_distribution': time_since_distribution,
            'time_remaining': time_remaining,
            'distribution_interval': self.distribution_interval,
            'distribution_percentages': self.fee_distribution,
            'accumulated_fees': self.accumulated_fees,
            'validator_rewards': self.validator_rewards
        }
    
    def get_distribution_history(self, start_time: float = None,
                               end_time: float = None,
                               limit: int = 50) -> List[Dict]:
        """
        Get distribution history.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of records to return
            
        Returns:
            List of distribution records
        """
        history = self.distribution_history.copy()
        
        if start_time:
            history = [d for d in history if d['timestamp'] >= start_time]
            
        if end_time:
            history = [d for d in history if d['timestamp'] <= end_time]
            
        history = sorted(history, key=lambda x: x['timestamp'], reverse=True)
        
        return history[:limit]
    
    def get_distribution_stats(self) -> Dict:
        """
        Get distribution statistics.
        
        Returns:
            Distribution statistics dictionary
        """
        if not self.distribution_history:
            return {
                'total_distributions': 0,
                'total_fees_distributed': 0,
                'avg_distribution_amount': 0,
                'avg_time_between_distributions': 0
            }
            
        total_fees = sum(d['total_amount'] for d in self.distribution_history)
        avg_amount = total_fees / len(self.distribution_history)
        
        time_between_distributions = []
        for i in range(1, len(self.distribution_history)):
            time_between = self.distribution_history[i]['timestamp'] - \
                          self.distribution_history[i-1]['timestamp']
            time_between_distributions.append(time_between)
            
        avg_time_between = sum(time_between_distributions) / len(time_between_distributions) \
                          if time_between_distributions else 0
        
        distribution_counts = {
            category: sum(d['distribution'][category] for d in self.distribution_history)
            for category in self.fee_distribution
        }
        
        return {
            'total_distributions': len(self.distribution_history),
            'total_fees_distributed': total_fees,
            'avg_distribution_amount': avg_amount,
            'avg_time_between_distributions': avg_time_between,
            'category_distribution': distribution_counts,
            'method_distribution': {
                'auto': len([d for d in self.distribution_history if d['method'] == 'auto']),
                'manual': len([d for d in self.distribution_history if d['method'] == 'manual'])
            }
        }
    
    def set_fee_distribution(self, distribution: Dict):
        """
        Set fee distribution percentages.
        
        Args:
            distribution: Dictionary of category to percentage (0-1)
            
        Raises:
            Exception: If distribution is invalid
        """
        total_percentage = sum(distribution.values())
        
        if not (0.99 <= total_percentage <= 1.01):
            raise Exception("Total fee distribution must sum to 100%")
            
        for category, percentage in distribution.items():
            if category not in self.fee_distribution:
                raise Exception(f"Unknown category: {category}")
                
            if not (0 <= percentage <= 1):
                raise Exception("Percentage must be between 0 and 1")
                
        self.fee_distribution.update(distribution)
    
    def set_minimum_distribution_amount(self, amount: int):
        """
        Set minimum distribution amount.
        
        Args:
            amount: Minimum fee amount
            
        Raises:
            Exception: If amount is invalid
        """
        if amount <= 0:
            raise Exception("Minimum distribution amount must be positive")
            
        self.minimum_distribution_amount = amount
    
    def set_distribution_interval(self, interval: int):
        """
        Set distribution interval.
        
        Args:
            interval: Interval in seconds
            
        Raises:
            Exception: If interval is invalid
        """
        if interval <= 0:
            raise Exception("Distribution interval must be positive")
            
        self.distribution_interval = interval
    
    def get_validator_rewards(self, validator_address: str = None) -> Dict:
        """
        Get validator rewards.
        
        Args:
            validator_address: Optional validator address filter
            
        Returns:
            Validator rewards dictionary
        """
        if validator_address:
            if validator_address not in self.validator_rewards:
                return {'validator_address': validator_address, 'reward': 0}
                
            return {
                'validator_address': validator_address,
                'reward': self.validator_rewards[validator_address]
            }
        else:
            return {
                'validators': [
                    {
                        'validator_address': address,
                        'reward': reward
                    }
                    for address, reward in self.validator_rewards.items()
                ],
                'total_rewards': sum(self.validator_rewards.values())
            }
    
    def get_stakeholder_distribution(self) -> Dict:
        """
        Get current fee distribution to each stakeholder category.
        
        Returns:
            Stakeholder distribution dictionary
        """
        return {
            category: {
                'percentage': percentage * 100,
                'accumulated_amount': self.accumulated_fees[category]
            }
            for category, percentage in self.fee_distribution.items()
        }
    
    def get_fee_collection_stats(self) -> Dict:
        """
        Get fee collection statistics.
        
        Returns:
            Fee collection statistics dictionary
        """
        current_period_fees = sum(self.accumulated_fees.values())
        
        if self.distribution_history:
            previous_periods = self.distribution_history[-7:]  # Last 7 distributions
            avg_fees_per_period = sum(d['total_amount'] for d in previous_periods) / len(previous_periods)
        else:
            avg_fees_per_period = 0
            
        time_since_distribution = time.time() - self.last_distribution_time
        fees_per_second = current_period_fees / time_since_distribution \
                        if time_since_distribution > 0 else 0
        
        estimated_fees = fees_per_second * self.distribution_interval
        
        return {
            'current_period_fees': current_period_fees,
            'avg_fees_per_period': avg_fees_per_period,
            'time_since_distribution': time_since_distribution,
            'fees_per_second': fees_per_second,
            'estimated_period_fees': estimated_fees
        }
    
    def __repr__(self):
        """String representation of the FeeDistributionSystem."""
        info = self.get_fee_distribution_info()
        return (f"FeeDistributionSystem(fees={info['total_fees']}, "
                f"next_distribution_in={info['time_remaining']:.0f} sec)")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_fee_distribution_info()
        stats = self.get_distribution_stats()
        stakeholder_dist = self.get_stakeholder_distribution()
        
        distribution_str = "\n".join([
            f"  {category}: {info['accumulated_fees'][category]} ({stakeholder_dist[category]['percentage']:.1f}%)" 
            for category in self.fee_distribution
        ])
        
        return (
            f"Fee Distribution System\n"
            f"======================\n"
            f"Total Fees: {info['total_fees']}\n"
            f"Minimum Distribution: {info['minimum_distribution_amount']}\n"
            f"Distribution Interval: {info['distribution_interval']} seconds\n"
            f"Time Since Last Distribution: {info['time_since_distribution']:.0f} sec\n"
            f"Time Remaining: {info['time_remaining']:.0f} sec\n"
            f"\nStakeholder Distribution:\n"
            f"{distribution_str}\n"
            f"\nStatistics:\n"
            f"Total Distributions: {stats['total_distributions']}\n"
            f"Total Fees Distributed: {stats['total_fees_distributed']}\n"
            f"Average Distribution Amount: {stats['avg_distribution_amount']:.2f}\n"
            f"Average Time Between Distributions: {stats['avg_time_between_distributions']:.0f} sec"
        )
