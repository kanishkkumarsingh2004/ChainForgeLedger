"""
ChainForgeLedger Staking & Reward Pool

Implements staking and reward distribution mechanisms.
"""

import time
from typing import Dict, List
from chainforgeledger.tokenomics.treasury import TreasuryManager


class StakingPool:
    """
    Staking pool implementation for managing validator staking and rewards.
    
    Attributes:
        total_stake: Total amount of coins staked
        validator_stakes: Dictionary of validator stakes
        delegator_stakes: Dictionary of delegator stakes per validator
        reward_pool: Total reward pool amount
        reward_distribution: Reward distribution parameters
        staking_period: Minimum staking period
        unstaking_lockup: Unstaking lockup period
        validator_commission: Validator commission rates
    """
    
    def __init__(self, treasury: TreasuryManager,
                 staking_period: int = 86400,
                 unstaking_lockup: int = 604800,
                 validator_commission: float = 0.1,
                 min_stake: int = 100):
        """
        Initialize a StakingPool instance.
        
        Args:
            treasury: Treasury manager for reward distribution
            staking_period: Minimum staking period in seconds
            unstaking_lockup: Unstaking lockup period in seconds
            validator_commission: Validator commission rate
            min_stake: Minimum stake required to become validator
        """
        self.treasury = treasury
        self.total_stake = 0
        self.validator_stakes: Dict[str, int] = {}
        self.delegator_stakes: Dict[str, Dict[str, int]] = {}
        self.reward_pool = 0
        self.staking_period = staking_period
        self.unstaking_lockup = unstaking_lockup
        self.validator_commission = validator_commission
        self.min_stake = min_stake
        self.staking_history: List[Dict] = []
        self.reward_history: List[Dict] = []
        self.unstaking_queue: List[Dict] = []
        self.reward_distribution = {
            'block_reward': 50,
            'transaction_fee_share': 0.5,
            'validator_share': 0.7,
            'delegator_share': 0.3
        }
    
    def stake(self, validator_address: str, staker_address: str, 
             amount: int) -> bool:
        """
        Stake coins to a validator.
        
        Args:
            validator_address: Validator address
            staker_address: Staker address
            amount: Amount to stake
            
        Returns:
            True if staking was successful
        """
        if amount < 1:
            return False
            
        # Check minimum stake if becoming a validator
        if validator_address == staker_address and amount < self.min_stake:
            return False
            
        # Add or update validator stake
        if validator_address not in self.validator_stakes:
            self.validator_stakes[validator_address] = 0
            self.delegator_stakes[validator_address] = {}
            
        # If staker is validator, update validator stake
        if validator_address == staker_address:
            self.validator_stakes[validator_address] += amount
        else:
            # If staker is delegator, update delegator stake
            if staker_address not in self.delegator_stakes[validator_address]:
                self.delegator_stakes[validator_address][staker_address] = 0
                
            self.delegator_stakes[validator_address][staker_address] += amount
            
        self.total_stake += amount
        
        # Record staking event
        self.staking_history.append({
            'validator_address': validator_address,
            'staker_address': staker_address,
            'amount': amount,
            'timestamp': time.time(),
            'type': 'stake'
        })
        
        return True
    
    def unstake(self, validator_address: str, staker_address: str, 
               amount: int) -> bool:
        """
        Unstake coins from a validator.
        
        Args:
            validator_address: Validator address
            staker_address: Staker address
            amount: Amount to unstake
            
        Returns:
            True if unstaking was successfully queued
        """
        if amount < 1:
            return False
            
        if validator_address not in self.validator_stakes:
            return False
            
        # Check available stake
        if validator_address == staker_address:
            if self.validator_stakes[validator_address] < amount:
                return False
        else:
            if staker_address not in self.delegator_stakes[validator_address] or \
               self.delegator_stakes[validator_address][staker_address] < amount:
                return False
                
        # Add to unstaking queue
        self.unstaking_queue.append({
            'validator_address': validator_address,
            'staker_address': staker_address,
            'amount': amount,
            'request_time': time.time(),
            'release_time': time.time() + self.unstaking_lockup,
            'completed': False
        })
        
        # Record unstaking event
        self.staking_history.append({
            'validator_address': validator_address,
            'staker_address': staker_address,
            'amount': -amount,
            'timestamp': time.time(),
            'type': 'unstake'
        })
        
        return True
    
    def process_unstaking(self) -> List[Dict]:
        """
        Process unstaking requests that have completed lockup period.
        
        Returns:
            List of processed unstaking transactions
        """
        current_time = time.time()
        processed = []
        
        for request in self.unstaking_queue:
            if not request['completed'] and current_time >= request['release_time']:
                # Remove stake from validator
                if request['validator_address'] == request['staker_address']:
                    self.validator_stakes[request['validator_address']] -= request['amount']
                else:
                    self.delegator_stakes[request['validator_address']][request['staker_address']] -= request['amount']
                    
                    # Remove delegator if stake is zero
                    if self.delegator_stakes[request['validator_address']][request['staker_address']] == 0:
                        del self.delegator_stakes[request['validator_address']][request['staker_address']]
                
                self.total_stake -= request['amount']
                request['completed'] = True
                processed.append(request)
        
        return processed
    
    def add_rewards(self, block_reward: int, transaction_fees: int) -> int:
        """
        Add rewards to the reward pool.
        
        Args:
            block_reward: Block reward to add
            transaction_fees: Transaction fees to add
            
        Returns:
            Total rewards added to pool
        """
        total_rewards = block_reward + int(transaction_fees * self.reward_distribution['transaction_fee_share'])
        self.reward_pool += total_rewards
        
        return total_rewards
    
    def distribute_rewards(self, block_height: int) -> List[Dict]:
        """
        Distribute rewards to validators and delegators.
        
        Args:
            block_height: Current block height
            
        Returns:
            List of reward distribution transactions
        """
        if self.reward_pool == 0 or self.total_stake == 0:
            return []
            
        # Calculate reward per staked coin
        reward_per_coin = self.reward_pool / self.total_stake
        
        distributions = []
        
        # Distribute rewards to each validator
        for validator_address, validator_stake in self.validator_stakes.items():
            validator_total_stake = validator_stake + sum(
                self.delegator_stakes[validator_address].values()
            )
            
            # Total rewards for this validator's pool
            validator_pool_rewards = validator_total_stake * reward_per_coin
            
            # Split into validator and delegator shares
            validator_rewards = validator_pool_rewards * self.reward_distribution['validator_share']
            delegator_rewards = validator_pool_rewards * self.reward_distribution['delegator_share']
            
            # Apply validator commission
            validator_commission = validator_rewards * self.validator_commission
            validator_net_rewards = validator_rewards - validator_commission
            
            # Distribute validator rewards
            distributions.append({
                'validator_address': validator_address,
                'recipient_address': validator_address,
                'amount': int(validator_net_rewards),
                'type': 'validator_reward',
                'block_height': block_height,
                'timestamp': time.time()
            })
            
            # Distribute delegator rewards
            for delegator_address, delegator_stake in self.delegator_stakes[validator_address].items():
                if delegator_address == validator_address:
                    continue
                    
                delegator_share = delegator_stake / validator_total_stake
                delegator_reward = delegator_rewards * delegator_share
                
                distributions.append({
                    'validator_address': validator_address,
                    'recipient_address': delegator_address,
                    'amount': int(delegator_reward),
                    'type': 'delegator_reward',
                    'block_height': block_height,
                    'timestamp': time.time()
                })
        
        # Reset reward pool
        self.reward_pool = 0
        
        # Record reward distribution
        for distribution in distributions:
            self.reward_history.append(distribution)
            
        return distributions
    
    def get_validator_stake(self, validator_address: str) -> int:
        """
        Get total stake for a validator (including delegators).
        
        Args:
            validator_address: Validator address
            
        Returns:
            Total stake for the validator
        """
        if validator_address not in self.validator_stakes:
            return 0
            
        return self.validator_stakes[validator_address] + sum(
            self.delegator_stakes[validator_address].values()
        )
    
    def get_staker_stake(self, validator_address: str, staker_address: str) -> int:
        """
        Get stake of a specific staker with a validator.
        
        Args:
            validator_address: Validator address
            staker_address: Staker address
            
        Returns:
            Stake of the staker with the validator
        """
        if validator_address == staker_address:
            return self.validator_stakes.get(validator_address, 0)
        else:
            return self.delegator_stakes.get(validator_address, {}).get(staker_address, 0)
    
    def get_validators(self) -> List[Dict]:
        """
        Get list of validators with their stake information.
        
        Returns:
            List of validator information dictionaries
        """
        validators = []
        
        for validator_address, validator_stake in self.validator_stakes.items():
            total_stake = self.get_validator_stake(validator_address)
            delegator_count = len(self.delegator_stakes[validator_address])
            
            validators.append({
                'validator_address': validator_address,
                'validator_stake': validator_stake,
                'delegator_stake': total_stake - validator_stake,
                'total_stake': total_stake,
                'delegator_count': delegator_count,
                'stake_percentage': total_stake / self.total_stake * 100 if self.total_stake > 0 else 0
            })
            
        # Sort by total stake (descending)
        return sorted(validators, key=lambda x: x['total_stake'], reverse=True)
    
    def get_delegators(self, validator_address: str) -> List[Dict]:
        """
        Get list of delegators for a validator.
        
        Args:
            validator_address: Validator address
            
        Returns:
            List of delegator information dictionaries
        """
        if validator_address not in self.delegator_stakes:
            return []
            
        delegators = []
        
        for delegator_address, stake in self.delegator_stakes[validator_address].items():
            if delegator_address == validator_address:
                continue
                
            delegators.append({
                'delegator_address': delegator_address,
                'stake': stake,
                'stake_percentage': stake / self.get_validator_stake(validator_address) * 100
            })
            
        # Sort by stake (descending)
        return sorted(delegators, key=lambda x: x['stake'], reverse=True)
    
    def get_staking_stats(self) -> Dict:
        """
        Get staking statistics.
        
        Returns:
            Staking statistics dictionary
        """
        validators = self.get_validators()
        active_validators = [v for v in validators if v['total_stake'] >= self.min_stake]
        
        total_delegators = sum(len(self.delegator_stakes[v]) - 1 for v in self.validator_stakes)
        
        avg_stake_per_validator = sum(v['total_stake'] for v in validators) / len(validators) if validators else 0
        avg_stake_per_delegator = self.total_stake / (total_delegators + len(validators)) if (total_delegators + len(validators)) > 0 else 0
        
        return {
            'total_stake': self.total_stake,
            'validator_count': len(validators),
            'active_validator_count': len(active_validators),
            'delegator_count': total_delegators,
            'avg_stake_per_validator': avg_stake_per_validator,
            'avg_stake_per_delegator': avg_stake_per_delegator,
            'reward_pool': self.reward_pool
        }
    
    def get_reward_stats(self) -> Dict:
        """
        Get reward distribution statistics.
        
        Returns:
            Reward distribution statistics dictionary
        """
        total_rewards = sum(r['amount'] for r in self.reward_history)
        validator_rewards = sum(r['amount'] for r in self.reward_history if r['type'] == 'validator_reward')
        delegator_rewards = sum(r['amount'] for r in self.reward_history if r['type'] == 'delegator_reward')
        
        distribution_counts = {
            'validator_reward': sum(1 for r in self.reward_history if r['type'] == 'validator_reward'),
            'delegator_reward': sum(1 for r in self.reward_history if r['type'] == 'delegator_reward')
        }
        
        avg_reward_per_distribution = total_rewards / sum(distribution_counts.values()) if sum(distribution_counts.values()) > 0 else 0
        
        return {
            'total_rewards': total_rewards,
            'validator_rewards': validator_rewards,
            'delegator_rewards': delegator_rewards,
            'distribution_counts': distribution_counts,
            'avg_reward_per_distribution': avg_reward_per_distribution
        }
    
    def set_reward_distribution(self, validator_share: float, 
                               delegator_share: float,
                               transaction_fee_share: float):
        """
        Set reward distribution parameters.
        
        Args:
            validator_share: Validator share of rewards
            delegator_share: Delegator share of rewards
            transaction_fee_share: Transaction fee share of rewards
        """
        if validator_share + delegator_share != 1:
            raise ValueError("Validator and delegator shares must sum to 1")
            
        if transaction_fee_share < 0 or transaction_fee_share > 1:
            raise ValueError("Transaction fee share must be between 0 and 1")
            
        self.reward_distribution = {
            'block_reward': self.reward_distribution['block_reward'],
            'transaction_fee_share': transaction_fee_share,
            'validator_share': validator_share,
            'delegator_share': delegator_share
        }
    
    def __repr__(self):
        """String representation of the StakingPool."""
        stats = self.get_staking_stats()
        return (f"StakingPool(total_stake={stats['total_stake']}, "
                f"validators={stats['validator_count']}, "
                f"reward_pool={stats['reward_pool']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_staking_stats()
        reward_stats = self.get_reward_stats()
        
        return (
            f"Staking Pool\n"
            f"============\n"
            f"Total Stake: {stats['total_stake']}\n"
            f"Validators: {stats['active_validator_count']}/{stats['validator_count']}\n"
            f"Delegators: {stats['delegator_count']}\n"
            f"Reward Pool: {stats['reward_pool']}\n"
            f"Total Rewards Distributed: {reward_stats['total_rewards']}\n"
            f"Validator Share: {reward_stats['validator_rewards']} ({reward_stats['validator_rewards']/reward_stats['total_rewards']*100:.1f}%)\n"
            f"Delegator Share: {reward_stats['delegator_rewards']} ({reward_stats['delegator_rewards']/reward_stats['total_rewards']*100:.1f}%)\n"
            f"Average Reward per Distribution: {reward_stats['avg_reward_per_distribution']:.2f}"
        )
