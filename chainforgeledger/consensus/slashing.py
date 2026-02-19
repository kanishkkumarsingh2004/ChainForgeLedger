"""
ChainForgeLedger Slashing Mechanism

Implements validator slashing for misbehavior.
"""

import time
from typing import Dict, List


class SlashingMechanism:
    """
    Implements validator slashing for misbehavior.
    
    Attributes:
        slash_reasons: Valid reasons for slashing
        slash_amounts: Default slash amounts per reason
        validator_history: History of validator behavior
        slashing_events: Record of all slashing events
    """
    
    SLASH_REASONS = [
        'double_signing',
        'validator_offline',
        'invalid_block',
        'proposal_manipulation',
        'vote_manipulation',
        'protocol_violation'
    ]
    
    DEFAULT_SLASH_AMOUNTS = {
        'double_signing': 0.5,       # 50% of stake
        'validator_offline': 0.05,   # 5% of stake
        'invalid_block': 0.25,       # 25% of stake
        'proposal_manipulation': 0.3, # 30% of stake
        'vote_manipulation': 0.2,    # 20% of stake
        'protocol_violation': 0.4    # 40% of stake
    }
    
    def __init__(self):
        """Initialize a SlashingMechanism instance."""
        self.validator_history = {}
        self.slashing_events = []
        self.slash_amounts = self.DEFAULT_SLASH_AMOUNTS.copy()
        self.offline_threshold = 3  # Consecutive blocks offline before slashing
        self.slash_cooldown = 86400  # 24 hours cooldown between slashes
    
    def record_validator_behavior(self, validator_address: str, behavior: str, 
                                 block_height: int = None):
        """
        Record validator behavior.
        
        Args:
            validator_address: Validator address
            behavior: Behavior type (e.g., 'online', 'offline', 'valid_block', 'invalid_block')
            block_height: Block height where behavior occurred
        """
        if validator_address not in self.validator_history:
            self.validator_history[validator_address] = {
                'offline_count': 0,
                'invalid_blocks': 0,
                'valid_blocks': 0,
                'last_slash_time': 0,
                'behavior_history': []
            }
        
        history = self.validator_history[validator_address]
        timestamp = time.time()
        behavior_info = {
            'timestamp': timestamp,
            'block_height': block_height,
            'behavior': behavior
        }
        
        history['behavior_history'].append(behavior_info)
        
        # Update counters
        if behavior == 'offline':
            history['offline_count'] += 1
        elif behavior == 'invalid_block':
            history['invalid_blocks'] += 1
        elif behavior == 'valid_block':
            history['valid_blocks'] += 1
            history['offline_count'] = 0  # Reset offline count
    
    def check_slashing_conditions(self, validator_address: str) -> List[str]:
        """
        Check if validator should be slashed based on behavior history.
        
        Args:
            validator_address: Validator address
            
        Returns:
            List of reasons validator should be slashed
        """
        if validator_address not in self.validator_history:
            return []
            
        history = self.validator_history[validator_address]
        current_time = time.time()
        
        # Check cooldown period
        if current_time - history['last_slash_time'] < self.slash_cooldown:
            return []
            
        reasons = []
        
        # Check offline slashing
        if history['offline_count'] >= self.offline_threshold:
            reasons.append('validator_offline')
        
        # Check invalid block slashing
        if history['invalid_blocks'] > 0:
            reasons.append('invalid_block')
            
        return reasons
    
    def slash_validator(self, validator_address: str, reason: str, 
                       amount: float = None, block_height: int = None) -> Dict:
        """
        Slash a validator.
        
        Args:
            validator_address: Validator address
            reason: Slashing reason
            amount: Amount to slash (percentage)
            block_height: Block height where slashing occurred
            
        Returns:
            Slashing event information
            
        Raises:
            ValueError: If reason is invalid
        """
        if reason not in self.SLASH_REASONS:
            raise ValueError(f"Invalid slashing reason: {reason}")
            
        # Check cooldown
        if validator_address in self.validator_history:
            current_time = time.time()
            if current_time - self.validator_history[validator_address]['last_slash_time'] < self.slash_cooldown:
                raise Exception("Slashing cooldown period not elapsed")
                
        # Determine slash amount
        if amount is None:
            amount = self.slash_amounts[reason]
            
        # Cap slash amount
        amount = max(0, min(1, amount))
        
        # Record slashing event
        slashing_event = {
            'validator_address': validator_address,
            'reason': reason,
            'amount': amount,
            'block_height': block_height,
            'timestamp': time.time()
        }
        
        self.slashing_events.append(slashing_event)
        
        # Update validator history
        if validator_address not in self.validator_history:
            self.validator_history[validator_address] = {
                'offline_count': 0,
                'invalid_blocks': 0,
                'valid_blocks': 0,
                'last_slash_time': 0,
                'behavior_history': []
            }
        
        self.validator_history[validator_address]['last_slash_time'] = slashing_event['timestamp']
        
        return slashing_event
    
    def get_slashing_events(self, validator_address: str = None, 
                           start_time: float = None, end_time: float = None) -> List[Dict]:
        """
        Get slashing events.
        
        Args:
            validator_address: Optional validator address filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of slashing events
        """
        events = self.slashing_events
        
        if validator_address:
            events = [e for e in events if e['validator_address'] == validator_address]
            
        if start_time:
            events = [e for e in events if e['timestamp'] >= start_time]
            
        if end_time:
            events = [e for e in events if e['timestamp'] <= end_time]
            
        return events
    
    def get_validator_slash_history(self, validator_address: str) -> Dict:
        """
        Get validator slashing history.
        
        Args:
            validator_address: Validator address
            
        Returns:
            Validator slashing history
        """
        events = self.get_slashing_events(validator_address=validator_address)
        history = self.validator_history.get(validator_address, {})
        
        return {
            'validator_address': validator_address,
            'slashing_events': events,
            'total_slash_amount': sum(event['amount'] for event in events),
            'last_slash_time': history.get('last_slash_time', 0),
            'offline_count': history.get('offline_count', 0),
            'invalid_blocks': history.get('invalid_blocks', 0),
            'valid_blocks': history.get('valid_blocks', 0)
        }
    
    def get_slash_statistics(self) -> Dict:
        """
        Get slashing statistics.
        
        Returns:
            Slashing statistics dictionary
        """
        if not self.slashing_events:
            return {
                'total_events': 0,
                'total_slash_amount': 0,
                'validators_slashed': 0,
                'events_per_reason': {}
            }
            
        # Calculate statistics
        validators_slashed = set(event['validator_address'] for event in self.slashing_events)
        events_per_reason = {}
        
        for reason in self.SLASH_REASONS:
            events_per_reason[reason] = len([
                e for e in self.slashing_events if e['reason'] == reason
            ])
        
        return {
            'total_events': len(self.slashing_events),
            'total_slash_amount': sum(event['amount'] for event in self.slashing_events),
            'validators_slashed': len(validators_slashed),
            'events_per_reason': events_per_reason
        }
    
    def set_slash_amount(self, reason: str, amount: float):
        """
        Set slash amount for a specific reason.
        
        Args:
            reason: Slashing reason
            amount: Slash amount (percentage between 0 and 1)
            
        Raises:
            ValueError: If reason is invalid or amount is out of range
        """
        if reason not in self.SLASH_REASONS:
            raise ValueError(f"Invalid slashing reason: {reason}")
            
        if amount < 0 or amount > 1:
            raise ValueError("Slash amount must be between 0 and 1")
            
        self.slash_amounts[reason] = amount
    
    def set_offline_threshold(self, threshold: int):
        """
        Set offline threshold for slashing.
        
        Args:
            threshold: Number of consecutive blocks offline before slashing
            
        Raises:
            ValueError: If threshold is invalid
        """
        if threshold < 1:
            raise ValueError("Offline threshold must be at least 1")
            
        self.offline_threshold = threshold
    
    def set_slash_cooldown(self, cooldown: int):
        """
        Set slashing cooldown period.
        
        Args:
            cooldown: Cooldown period in seconds
            
        Raises:
            ValueError: If cooldown is invalid
        """
        if cooldown < 0:
            raise ValueError("Slash cooldown must be non-negative")
            
        self.slash_cooldown = cooldown
    
    def clear_behavior_history(self, validator_address: str):
        """
        Clear validator behavior history.
        
        Args:
            validator_address: Validator address
        """
        if validator_address in self.validator_history:
            self.validator_history[validator_address]['behavior_history'] = []
            self.validator_history[validator_address]['offline_count'] = 0
            self.validator_history[validator_address]['invalid_blocks'] = 0
    
    def is_validator_eligible(self, validator_address: str) -> bool:
        """
        Check if validator is eligible to participate in consensus.
        
        Args:
            validator_address: Validator address
            
        Returns:
            True if validator is eligible
        """
        if validator_address not in self.validator_history:
            return True
            
        history = self.validator_history[validator_address]
        
        # Check if validator has been slashed recently
        current_time = time.time()
        if current_time - history['last_slash_time'] < self.slash_cooldown:
            return False
            
        return True
    
    def __repr__(self):
        """String representation of the SlashingMechanism."""
        stats = self.get_slash_statistics()
        return (f"SlashingMechanism(events={stats['total_events']}, "
                f"validators_slashed={stats['validators_slashed']})")
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_slash_statistics()
        return (
            f"Slashing Mechanism\n"
            f"==================\n"
            f"Total Slashing Events: {stats['total_events']}\n"
            f"Validators Slashed: {stats['validators_slashed']}\n"
            f"Total Slash Amount: {stats['total_slash_amount']:.1%}\n"
            f"Offline Threshold: {self.offline_threshold} blocks\n"
            f"Slash Cooldown: {self.slash_cooldown} seconds"
        )
