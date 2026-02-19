"""
ChainForgeLedger Pluggable Consensus Interface

A unified interface for multiple consensus mechanisms with pluggable architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, List
from chainforgeledger.core.block import Block
from chainforgeledger.core.transaction import Transaction


class ConsensusInterface(ABC):
    """
    Abstract base class for consensus mechanisms.
    
    Defines a common interface for all consensus mechanisms,
    allowing them to be pluggable and interchangeable.
    """
    
    @abstractmethod
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """
        Validate a block according to the consensus rules.
        
        Args:
            block: Block to validate
            previous_block: Previous block in the chain
            
        Returns:
            True if block is valid, False otherwise
        """
        
    @abstractmethod
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """
        Mine a new block according to the consensus rules.
        
        Args:
            transactions: List of transactions to include
            previous_block: Previous block in the chain
            
        Returns:
            Newly mined block
        """
        
    @abstractmethod
    def calculate_reward(self, block: Block) -> float:
        """
        Calculate the reward for mining a block.
        
        Args:
            block: Block that was mined
            
        Returns:
            Reward amount
        """
        
    @abstractmethod
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """
        Check if consensus has been achieved across the network.
        
        Args:
            chain: Local chain copy
            peers: List of connected peers
            
        Returns:
            True if consensus is achieved
        """
        
    @abstractmethod
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """
        Select a validator for block production.
        
        Args:
            candidates: List of valid validator addresses
            block: Previous block
            
        Returns:
            Selected validator address
        """


class ProofOfWorkInterface(ConsensusInterface):
    """
    Proof of Work consensus interface.
    """
    
    def __init__(self, difficulty: int = 3):
        """
        Initialize PoW consensus.
        
        Args:
            difficulty: Mining difficulty level
        """
        self.difficulty = difficulty
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate PoW block."""
        # Check proof of work
        prefix = '0' * self.difficulty
        if not block.hash.startswith(prefix):
            return False
            
        # Validate block structure
        if block.previous_hash != previous_block.hash:
            return False
            
        if block.index != previous_block.index + 1:
            return False
            
        return True
        
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """Mine block using PoW."""
        from chainforgeledger.consensus.pow import ProofOfWork
        pow = ProofOfWork(self.difficulty)
        return pow.mine_block(transactions, previous_block)
        
    def calculate_reward(self, block: Block) -> float:
        """Calculate PoW reward."""
        return 50.0  # Fixed block reward
        
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """Check PoW consensus."""
        # In PoW, longest chain usually wins
        if len(peers) == 0:
            return True
            
        return True  # Simplified check
        
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """Select validator (miner) via PoW competition."""
        # In PoW, miner who finds block is selected
        return "pow_miner"


class ProofOfStakeInterface(ConsensusInterface):
    """
    Proof of Stake consensus interface.
    """
    
    def __init__(self, validator_manager: Any):
        """
        Initialize PoS consensus.
        
        Args:
            validator_manager: Validator management system
        """
        self.validator_manager = validator_manager
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate PoS block."""
        # Check validator signature
        if not self.validator_manager.validate_block(block):
            return False
            
        # Validate block structure
        if block.previous_hash != previous_block.hash:
            return False
            
        if block.index != previous_block.index + 1:
            return False
            
        return True
        
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """Mine block using PoS."""
        from chainforgeledger.consensus.pos import ProofOfStake
        pos = ProofOfStake(self.validator_manager)
        return pos.mine_block(transactions, previous_block)
        
    def calculate_reward(self, block: Block) -> float:
        """Calculate PoS reward."""
        return 25.0  # Fixed block reward plus transaction fees
        
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """Check PoS consensus."""
        # In PoS, validators need to agree
        if len(peers) == 0:
            return True
            
        return True  # Simplified check
        
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """Select validator based on stake."""
        return self.validator_manager.select_validator(block)


class DelegatedProofOfStakeInterface(ConsensusInterface):
    """
    Delegated Proof of Stake consensus interface.
    """
    
    def __init__(self, delegate_manager: Any):
        """
        Initialize DPoS consensus.
        
        Args:
            delegate_manager: Delegate management system
        """
        self.delegate_manager = delegate_manager
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate DPoS block."""
        # Check delegate signature
        if not self.delegate_manager.validate_block(block):
            return False
            
        # Validate block structure
        if block.previous_hash != previous_block.hash:
            return False
            
        if block.index != previous_block.index + 1:
            return False
            
        return True
        
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """Mine block using DPoS."""
        delegate = self.delegate_manager.select_delegate()
        from chainforgeledger.core.block import Block
        
        new_block = Block(
            index=previous_block.index + 1,
            previous_hash=previous_block.hash,
            transactions=transactions,
            validator=delegate
        )
        
        return new_block
        
    def calculate_reward(self, block: Block) -> float:
        """Calculate DPoS reward."""
        return 15.0  # Lower reward with delegation
        
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """Check DPoS consensus."""
        # In DPoS, delegates agree
        if len(peers) == 0:
            return True
            
        return True  # Simplified check
        
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """Select validator (delegate) via voting."""
        return self.delegate_manager.select_delegate()


class PBFTInterface(ConsensusInterface):
    """
    Practical Byzantine Fault Tolerance consensus interface.
    """
    
    def __init__(self, validator_manager: Any, f: int = 1):
        """
        Initialize PBFT consensus.
        
        Args:
            validator_manager: Validator management system
            f: Maximum number of Byzantine nodes
        """
        self.validator_manager = validator_manager
        self.f = f
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate PBFT block."""
        # Check Byzantine agreement signatures
        return True  # Simplified check
        
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """Mine block using PBFT."""
        from chainforgeledger.core.block import Block
        
        new_block = Block(
            index=previous_block.index + 1,
            previous_hash=previous_block.hash,
            transactions=transactions
        )
        
        return new_block
        
    def calculate_reward(self, block: Block) -> float:
        """Calculate PBFT reward."""
        return 10.0  # Lower reward due to faster consensus
        
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """Check PBFT consensus."""
        # In PBFT, require 2f+1 agreement
        agreement = self._collect_agreements(chain, peers)
        return len(agreement) >= 2 * self.f + 1
        
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """Select validator via PBFT rotation."""
        # Rotate validators in round-robin fashion
        round_num = block.index % len(candidates)
        return candidates[round_num]
        
    def _collect_agreements(self, chain: List[Block], peers: List[Any]) -> List[str]:
        """Collect agreements from peers."""
        agreements = []
        # Simplified agreement collection
        return agreements


class ConsensusFactory:
    """
    Factory for creating consensus mechanism instances.
    """
    
    @staticmethod
    def create(consensus_type: str, **kwargs) -> ConsensusInterface:
        """
        Create a consensus mechanism instance.
        
        Args:
            consensus_type: Type of consensus ('pow', 'pos', 'dpos', 'pbft')
            **kwargs: Additional arguments for specific consensus types
            
        Returns:
            ConsensusInterface instance
            
        Raises:
            ValueError: If consensus type is not recognized
        """
        if consensus_type == 'pow':
            difficulty = kwargs.get('difficulty', 3)
            return ProofOfWorkInterface(difficulty)
            
        elif consensus_type == 'pos':
            validator_manager = kwargs.get('validator_manager')
            return ProofOfStakeInterface(validator_manager)
            
        elif consensus_type == 'dpos':
            delegate_manager = kwargs.get('delegate_manager')
            return DelegatedProofOfStakeInterface(delegate_manager)
            
        elif consensus_type == 'pbft':
            validator_manager = kwargs.get('validator_manager')
            f = kwargs.get('f', 1)
            return PBFTInterface(validator_manager, f)
            
        else:
            raise ValueError(f"Unknown consensus type: {consensus_type}")


class ConsensusManager:
    """
    Manages consensus mechanism selection and switching.
    """
    
    def __init__(self, initial_consensus: str = 'pow', **kwargs):
        """
        Initialize consensus manager.
        
        Args:
            initial_consensus: Initial consensus type
            **kwargs: Configuration for consensus mechanisms
        """
        self.current_consensus = None
        self.consensus_mechanisms = {}
        self.kwargs = kwargs
        
        # Create initial consensus mechanism
        self.switch_consensus(initial_consensus)
        
    def switch_consensus(self, consensus_type: str):
        """
        Switch to a different consensus mechanism.
        
        Args:
            consensus_type: New consensus type to use
        """
        if consensus_type not in self.consensus_mechanisms:
            self.consensus_mechanisms[consensus_type] = ConsensusFactory.create(
                consensus_type, **self.kwargs
            )
            
        self.current_consensus = self.consensus_mechanisms[consensus_type]
        print(f"Switched to {consensus_type} consensus")
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate block using current consensus."""
        return self.current_consensus.validate_block(block, previous_block)
        
    def mine_block(self, transactions: List[Transaction], previous_block: Block) -> Block:
        """Mine block using current consensus."""
        return self.current_consensus.mine_block(transactions, previous_block)
        
    def calculate_reward(self, block: Block) -> float:
        """Calculate reward using current consensus."""
        return self.current_consensus.calculate_reward(block)
        
    def is_consensus_achieved(self, chain: List[Block], peers: List[Any]) -> bool:
        """Check consensus using current mechanism."""
        return self.current_consensus.is_consensus_achieved(chain, peers)
        
    def select_validator(self, candidates: List[str], block: Block) -> str:
        """Select validator using current consensus."""
        return self.current_consensus.select_validator(candidates, block)
