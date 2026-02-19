"""
ChainForgeLedger Validator Module

Validator management for PoS consensus.
"""

from typing import Optional, List
import random


class Validator:
    """
    Represents a blockchain validator.
    
    Attributes:
        address: Validator's address
        stake: Staked amount
        reputation: Reputation score
        blocks_produced: Number of blocks produced
        status: Validator status
    """
    
    def __init__(self, address: str, stake: float = 0.0):
        """
        Initialize a new Validator instance.
        
        Args:
            address: Validator's address
            stake: Initial staked amount
        """
        self.address = address
        self.stake = stake
        self.reputation = 1.0
        self.blocks_produced = 0
        self.status = "active"
        self.last_seen = 0
    
    def update_stake(self, amount: float):
        """
        Update staked amount.
        
        Args:
            amount: Amount to add (can be negative)
        """
        self.stake = max(0.0, self.stake + amount)
    
    def increase_reputation(self, amount: float):
        """
        Increase validator reputation.
        
        Args:
            amount: Amount to increase reputation
        """
        self.reputation = min(5.0, self.reputation + amount)
    
    def decrease_reputation(self, amount: float):
        """
        Decrease validator reputation.
        
        Args:
            amount: Amount to decrease reputation
        """
        self.reputation = max(0.0, self.reputation - amount)
    
    def produce_block(self):
        """Mark validator as having produced a block."""
        self.blocks_produced += 1
        self.increase_reputation(0.1)
    
    def mark_inactive(self):
        """Mark validator as inactive."""
        self.status = "inactive"
        self.decrease_reputation(0.5)
    
    def mark_active(self):
        """Mark validator as active."""
        self.status = "active"
    
    def is_active(self) -> bool:
        """Check if validator is active."""
        return self.status == "active"
    
    def get_effective_stake(self) -> float:
        """Get effective stake (stake * reputation)."""
        return self.stake * self.reputation
    
    def to_dict(self) -> dict:
        """
        Convert validator to dictionary.
        
        Returns:
            Dictionary representation of validator
        """
        return {
            "address": self.address,
            "stake": self.stake,
            "reputation": self.reputation,
            "blocks_produced": self.blocks_produced,
            "status": self.status,
            "last_seen": self.last_seen,
            "effective_stake": self.get_effective_stake()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Validator":
        """
        Create validator from dictionary.
        
        Args:
            data: Validator data
            
        Returns:
            Validator instance
        """
        validator = cls(data.get("address", ""), data.get("stake", 0.0))
        validator.reputation = data.get("reputation", 1.0)
        validator.blocks_produced = data.get("blocks_produced", 0)
        validator.status = data.get("status", "active")
        validator.last_seen = data.get("last_seen", 0)
        
        return validator
    
    def __repr__(self):
        """String representation of validator."""
        return (
            f"Validator(address={self.address[:16]}..., "
            f"stake={self.stake:.2f}, reputation={self.reputation:.2f})"
        )
    
    def __str__(self):
        """String representation for printing."""
        return (
            f"Validator: {self.address}\n"
            f"Stake: {self.stake:.2f}\n"
            f"Reputation: {self.reputation:.2f}\n"
            f"Blocks Produced: {self.blocks_produced}\n"
            f"Status: {self.status}\n"
            f"Effective Stake: {self.get_effective_stake():.2f}"
        )


class ValidatorManager:
    """
    Manages validator pool.
    
    Attributes:
        validators: Dictionary of validators
    """
    
    def __init__(self):
        """Initialize validator manager with empty pool."""
        self.validators = {}
    
    def add_validator(self, validator: Validator):
        """
        Add a validator to the pool.
        
        Args:
            validator: Validator to add
        """
        self.validators[validator.address] = validator
    
    def remove_validator(self, address: str) -> bool:
        """
        Remove a validator from the pool.
        
        Args:
            address: Validator address
            
        Returns:
            True if successful
        """
        if address in self.validators:
            del self.validators[address]
            return True
        return False
    
    def get_validator(self, address: str) -> Optional[Validator]:
        """
        Get a validator by address.
        
        Args:
            address: Validator address
            
        Returns:
            Validator if exists
        """
        return self.validators.get(address)
    
    def get_all_validators(self) -> List[Validator]:
        """
        Get all validators.
        
        Returns:
            List of validators
        """
        return list(self.validators.values())
    
    def get_active_validators(self) -> List[Validator]:
        """
        Get active validators.
        
        Returns:
            List of active validators
        """
        return [v for v in self.validators.values() if v.is_active()]
    
    def get_total_stake(self) -> float:
        """
        Get total staked amount.
        
        Returns:
            Total staked amount
        """
        return sum(v.stake for v in self.validators.values())
    
    def select_validator(self) -> Optional[Validator]:
        """
        Select validator based on stake and reputation.
        
        Returns:
            Selected validator
        """
        active_validators = self.get_active_validators()
        
        if not active_validators:
            return None
        
        # Weight by effective stake
        total_effective_stake = sum(v.get_effective_stake() for v in active_validators)
        random_value = random.uniform(0, total_effective_stake)
        current = 0.0
        
        for validator in active_validators:
            current += validator.get_effective_stake()
            if random_value <= current:
                return validator
        
        return active_validators[0]
    
    def update_validator_status(self, address: str, active: bool):
        """
        Update validator status.
        
        Args:
            address: Validator address
            active: New status
        """
        validator = self.get_validator(address)
        if validator:
            if active:
                validator.mark_active()
            else:
                validator.mark_inactive()
    
    def to_dict(self) -> dict:
        """
        Convert manager to dictionary.
        
        Returns:
            Dictionary representation of manager
        """
        return {
            "total_validators": len(self.validators),
            "active_validators": len(self.get_active_validators()),
            "total_stake": self.get_total_stake(),
            "validators": {addr: v.to_dict() for addr, v in self.validators.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ValidatorManager":
        """
        Create manager from dictionary.
        
        Args:
            data: Manager data
            
        Returns:
            ValidatorManager instance
        """
        manager = cls()
        for addr, validator_data in data.get("validators", {}).items():
            validator = Validator.from_dict(validator_data)
            manager.add_validator(validator)
        
        return manager
    
    def __repr__(self):
        """String representation of validator manager."""
        return (
            f"ValidatorManager(validators={len(self.validators)}, "
            f"active={len(self.get_active_validators())}, "
            f"total_stake={self.get_total_stake():,.2f})"
        )
    
    def __str__(self):
        """String representation for printing."""
        return (
            f"Validator Manager\n"
            f"=================\n"
            f"Total Validators: {len(self.validators)}\n"
            f"Active Validators: {len(self.get_active_validators())}\n"
            f"Total Stake: {self.get_total_stake():,.2f}\n"
            f"Average Stake: {self.get_total_stake() / len(self.validators):,.2f}"
        )
