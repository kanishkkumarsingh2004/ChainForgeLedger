"""
ChainForgeLedger DAO Module

Decentralized Autonomous Organization (DAO) implementation for blockchain governance.
"""

import time
import json
from typing import Dict, List, Optional
from chainforgeledger.utils.logger import get_logger
from chainforgeledger.governance.proposal import Proposal
from chainforgeledger.governance.voting import VotingSystem
from chainforgeledger.crypto.hashing import sha256_hash


class DAO:
    """
    Decentralized Autonomous Organization (DAO) for blockchain governance.
    
    Represents a democratic organization governed by token holders.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize DAO.
        
        Args:
            **kwargs: DAO configuration
        """
        # Initialize name first since it's used for ID generation
        self.name = kwargs.get('name', 'ChainForge DAO')
        self.dao_id = kwargs.get('dao_id', self._generate_dao_id())
        self.description = kwargs.get('description', 'Decentralized autonomous organization')
        self.creator_address = kwargs.get('creator_address', '')
        self.total_token_supply = kwargs.get('total_token_supply', 0)
        self.quorum_threshold = kwargs.get('quorum_threshold', 0.5)
        self.approval_threshold = kwargs.get('approval_threshold', 0.66)
        self.voting_period = kwargs.get('voting_period', 86400)
        self.proposal_fee = kwargs.get('proposal_fee', 0)
        self.governance_token = kwargs.get('governance_token', 'CFD')
        self.voting_system = VotingSystem()
        self.treasury = kwargs.get('treasury', {})
        self.members = kwargs.get('members', {})
        self.config = kwargs.get('config', {})
        self.created_at = kwargs.get('created_at', self._get_current_timestamp())
        self.updated_at = kwargs.get('updated_at', self._get_current_timestamp())
        self.logger = get_logger(__name__)
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp in seconds."""
        return time.time()
    
    def _generate_dao_id(self) -> str:
        """Generate unique DAO ID."""
        timestamp = self._get_current_timestamp()
        unique_id = sha256_hash(f"{timestamp}-{self.name}")
        return unique_id[:16]
    
    def validate(self) -> bool:
        """
        Validate DAO configuration.
        
        Returns:
            True if DAO is valid, False otherwise
        """
        validation_rules = [
            (isinstance(self.name, str) and len(self.name.strip()) > 0),
            (isinstance(self.creator_address, str) and len(self.creator_address.strip()) > 0),
            (isinstance(self.total_token_supply, (int, float)) and self.total_token_supply > 0),
            (isinstance(self.quorum_threshold, (int, float)) and 0 <= self.quorum_threshold <= 1),
            (isinstance(self.approval_threshold, (int, float)) and 0 <= self.approval_threshold <= 1),
            (isinstance(self.voting_period, (int, float)) and self.voting_period > 0)
        ]
        
        return all(validation_rules)
    
    def add_member(self, address: str, token_balance: float = 0):
        """
        Add a member to the DAO.
        
        Args:
            address: Member address
            token_balance: Token balance
        """
        try:
            if address in self.members:
                raise ValueError(f"Member {address} already exists")
            
            self.members[address] = token_balance
            self.voting_system.update_staking_power(address, token_balance)
            
            self.updated_at = self._get_current_timestamp()
            
            self.logger.info(f"Member added: {address}")
            
        except Exception as e:
            self.logger.error(f"Failed to add member: {e}")
            raise
    
    def remove_member(self, address: str):
        """
        Remove a member from the DAO.
        
        Args:
            address: Member address
        """
        try:
            if address not in self.members:
                raise ValueError(f"Member {address} not found")
            
            del self.members[address]
            self.voting_system.remove_staking_power(address)
            
            self.updated_at = self._get_current_timestamp()
            
            self.logger.info(f"Member removed: {address}")
            
        except Exception as e:
            self.logger.error(f"Failed to remove member: {e}")
            raise
    
    def update_member_balance(self, address: str, new_balance: float):
        """
        Update member's token balance.
        
        Args:
            address: Member address
            new_balance: New token balance
        """
        try:
            if address not in self.members:
                raise ValueError(f"Member {address} not found")
            
            old_balance = self.members[address]
            self.members[address] = new_balance
            self.voting_system.update_staking_power(address, new_balance)
            
            self.updated_at = self._get_current_timestamp()
            
            self.logger.info(f"Member balance updated: {address} {old_balance} -> {new_balance}")
            
        except Exception as e:
            self.logger.error(f"Failed to update member balance: {e}")
            raise
    
    def create_proposal(self, **kwargs) -> Proposal:
        """
        Create a new governance proposal.
        
        Args:
            **kwargs: Proposal attributes
            
        Returns:
            Created proposal instance
        """
        try:
            if 'proposer_address' not in kwargs:
                raise ValueError("Proposer address must be specified")
            
            if kwargs['proposer_address'] not in self.members:
                raise ValueError(f"Proposer {kwargs['proposer_address']} is not a DAO member")
            
            # Set default proposal parameters from DAO configuration
            kwargs.setdefault('quorum_required', self.quorum_threshold)
            kwargs.setdefault('approval_threshold', self.approval_threshold)
            
            proposal = self.voting_system.create_proposal(**kwargs)
            
            self.updated_at = self._get_current_timestamp()
            
            self.logger.info(f"Proposal created: {proposal.proposal_id}")
            return proposal
            
        except Exception as e:
            self.logger.error(f"Failed to create proposal: {e}")
            raise
    
    def submit_proposal(self, proposer_address: str, title: str, description: str, **kwargs) -> Proposal:
        """
        Submit a new proposal to the DAO.
        
        Args:
            proposer_address: Proposer address
            title: Proposal title
            description: Proposal description
            **kwargs: Additional proposal parameters
            
        Returns:
            Created proposal instance
        """
        return self.create_proposal(
            proposer_address=proposer_address,
            title=title,
            description=description,
            **kwargs
        )
    
    def activate_proposal(self, proposal_id: str, voting_duration: int = None):
        """
        Activate proposal for voting.
        
        Args:
            proposal_id: Proposal ID
            voting_duration: Voting duration in seconds
        """
        try:
            duration = voting_duration or self.voting_period
            self.voting_system.activate_proposal(proposal_id, duration)
            self.updated_at = self._get_current_timestamp()
            
        except Exception as e:
            self.logger.error(f"Failed to activate proposal: {e}")
            raise
    
    def finalize_proposal(self, proposal_id: str):
        """
        Finalize proposal after voting period ends.
        
        Args:
            proposal_id: Proposal ID
        """
        try:
            self.voting_system.finalize_proposal(proposal_id)
            self.updated_at = self._get_current_timestamp()
            
        except Exception as e:
            self.logger.error(f"Failed to finalize proposal: {e}")
            raise
    
    def execute_proposal(self, proposal_id: str):
        """
        Execute passed proposal.
        
        Args:
            proposal_id: Proposal ID
        """
        try:
            self.voting_system.execute_proposal(proposal_id)
            self.updated_at = self._get_current_timestamp()
            
        except Exception as e:
            self.logger.error(f"Failed to execute proposal: {e}")
            raise
    
    def cast_vote(self, proposal_id: str, voter_address: str, vote: str):
        """
        Cast a vote on a proposal.
        
        Args:
            proposal_id: Proposal ID
            voter_address: Voter address
            vote: Vote choice (yes/no/abstain)
        """
        try:
            if voter_address not in self.members:
                raise ValueError(f"Voter {voter_address} is not a DAO member")
            
            voting_power = self.members[voter_address]
            self.voting_system.cast_vote(proposal_id, voter_address, vote, voting_power)
            self.updated_at = self._get_current_timestamp()
            
        except Exception as e:
            self.logger.error(f"Failed to cast vote: {e}")
            raise
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """
        Get proposal by ID.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal instance or None if not found
        """
        return self.voting_system.get_proposal(proposal_id)
    
    def get_proposals(self, state: str = None, proposal_type: str = None) -> List[Proposal]:
        """
        Get all proposals.
        
        Args:
            state: Optional state filter
            proposal_type: Optional type filter
            
        Returns:
            List of proposals
        """
        return self.voting_system.get_proposals(state, proposal_type)
    
    def get_member_votes(self, address: str) -> List[Dict]:
        """
        Get all votes cast by a specific address.
        
        Args:
            address: Member address
            
        Returns:
            List of votes
        """
        return self.voting_system.get_voter_proposals(address)
    
    def get_proposal_summary(self, proposal_id: str) -> Dict:
        """
        Get proposal summary.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal summary
        """
        return self.voting_system.get_vote_summary(proposal_id)
    
    def get_stats(self) -> Dict:
        """
        Get DAO statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            proposal_stats = self.voting_system.get_proposal_stats()
            vote_stats = self.voting_system.get_vote_stats()
            
            return {
                "dao_id": self.dao_id,
                "name": self.name,
                "members": len(self.members),
                "total_token_supply": self.total_token_supply,
                "proposals": proposal_stats,
                "votes": vote_stats,
                "treasury": self.treasury,
                "config": {
                    "quorum": self.quorum_threshold,
                    "approval": self.approval_threshold,
                    "voting_period": self.voting_period,
                    "proposal_fee": self.proposal_fee
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get DAO stats: {e}")
            return {}
    
    def get_member_stats(self) -> Dict:
        """
        Get member statistics.
        
        Returns:
            Member statistics dictionary
        """
        try:
            total_staking_power = sum(self.members.values())
            average_balance = total_staking_power / len(self.members) if self.members else 0
            max_balance = max(self.members.values()) if self.members else 0
            min_balance = min(self.members.values()) if self.members else 0
            
            return {
                "count": len(self.members),
                "total_staking_power": total_staking_power,
                "average_balance": average_balance,
                "max_balance": max_balance,
                "min_balance": min_balance
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get member stats: {e}")
            return {}
    
    def update_config(self, **kwargs):
        """
        Update DAO configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        try:
            config_validators = {
                'quorum_threshold': lambda v: isinstance(v, (int, float)) and 0 <= v <= 1,
                'approval_threshold': lambda v: isinstance(v, (int, float)) and 0 <= v <= 1,
                'voting_period': lambda v: isinstance(v, (int, float)) and v >= 0,
                'proposal_fee': lambda v: isinstance(v, (int, float)) and v >= 0
            }
            
            for key, value in kwargs.items():
                if key in config_validators:
                    if not config_validators[key](value):
                        if key in ['quorum_threshold', 'approval_threshold']:
                            raise ValueError(f"Invalid {key} value: must be between 0 and 1")
                        else:
                            raise ValueError(f"Invalid {key} value: must be non-negative")
                    setattr(self, key, value)
                
            self.updated_at = self._get_current_timestamp()
            self.logger.info("DAO configuration updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update DAO config: {e}")
            raise
    
    def sync_with_blockchain(self, block_height: int):
        """
        Sync DAO with blockchain state.
        
        Args:
            block_height: Current block height
        """
        try:
            self.voting_system.sync_with_blockchain(block_height)
            self.updated_at = self._get_current_timestamp()
            
            self.logger.debug(f"DAO synced to block height: {block_height}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync DAO: {e}")
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary.
        
        Returns:
            DAO as dictionary
        """
        return {
            'dao_id': self.dao_id,
            'name': self.name,
            'description': self.description,
            'creator_address': self.creator_address,
            'total_token_supply': self.total_token_supply,
            'quorum_threshold': self.quorum_threshold,
            'approval_threshold': self.approval_threshold,
            'voting_period': self.voting_period,
            'proposal_fee': self.proposal_fee,
            'governance_token': self.governance_token,
            'voting_system': self.voting_system.to_dict(),
            'treasury': self.treasury,
            'members': self.members,
            'config': self.config,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def to_json(self) -> str:
        """
        Convert to JSON string.
        
        Returns:
            DAO as JSON string
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DAO':
        """
        Create from dictionary.
        
        Args:
            data: DAO data
            
        Returns:
            DAO instance
        """
        dao = cls(**data)
        dao.voting_system.from_dict(data.get('voting_system', {}))
        return dao
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DAO':
        """
        Create from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            DAO instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __repr__(self):
        """String representation."""
        return f"DAO(id={self.dao_id}, name=\"{self.name}\")"
    
    def __str__(self):
        """String representation for printing."""
        stats = self.get_stats()
        
        return (
            f"{self.name} ({self.dao_id})\n"
            f"==================\n"
            f"Description: {self.description}\n"
            f"Creator: {self.creator_address}\n"
            f"Members: {stats['members']}\n"
            f"Token Supply: {stats['total_token_supply']:.0f} {self.governance_token}\n"
            f"Proposals: {stats['proposals']['total']}\n"
            f"Active Proposals: {stats['proposals']['states'].get('active', 0)}\n"
            f"Treasury: {json.dumps(self.treasury, indent=2)}\n"
            f"Config: Quorum={self.quorum_threshold:.0%}, Approval={self.approval_threshold:.0%}\n"
            f"Created: {self.created_at}"
        )
