"""
ChainForgeLedger Treasury Management Module

Manages the blockchain treasury and funding operations.
"""

import time
from typing import Dict, List, Optional
from chainforgeledger.crypto.hashing import sha256_hash
from chainforgeledger.governance.dao import DAO


class TreasuryManager:
    """
    Manages the blockchain treasury and funding operations.
    
    Attributes:
        treasury_address: Treasury wallet address
        balance: Current treasury balance
        transactions: History of treasury transactions
        funding_proposals: Active funding proposals
        approved_proposals: Approved funding proposals
        rejected_proposals: Rejected funding proposals
        dao: DAO instance for governance
        proposal_fee: Fee required to submit a funding proposal
        minimum_proposal_amount: Minimum proposal amount
    """
    
    def __init__(self, dao: DAO, treasury_address: str = None):
        """
        Initialize a TreasuryManager instance.
        
        Args:
            dao: DAO instance for governance
            treasury_address: Optional treasury address
        """
        self.dao = dao
        self.treasury_address = treasury_address or self._generate_treasury_address()
        self.balance = 0
        self.transactions = []
        self.funding_proposals = []
        self.approved_proposals = []
        self.rejected_proposals = []
        self.proposal_fee = 0.01  # 1% of proposal amount
        self.minimum_proposal_amount = 100
        self.transaction_counter = 0
    
    def _generate_treasury_address(self) -> str:
        """Generate unique treasury address."""
        data = f"treasury:{self.dao.dao_id}:{time.time()}"
        return sha256_hash(data)[:32]
    
    def submit_funding_proposal(self, proposer_address: str, title: str, 
                               description: str, amount: float, 
                               recipient_address: str) -> Dict:
        """
        Submit a funding proposal.
        
        Args:
            proposer_address: Proposer address
            title: Proposal title
            description: Proposal description
            amount: Funding amount
            recipient_address: Recipient address
            
        Returns:
            Created proposal dictionary
            
        Raises:
            Exception: If proposal submission fails
        """
        if amount < self.minimum_proposal_amount:
            raise Exception(f"Proposal amount must be at least {self.minimum_proposal_amount}")
            
        # Calculate proposal fee
        fee = amount * self.proposal_fee
        
        # Create proposal
        proposal = {
            'proposal_id': self._generate_proposal_id(),
            'proposer_address': proposer_address,
            'title': title,
            'description': description,
            'amount': amount,
            'fee': fee,
            'recipient_address': recipient_address,
            'status': 'pending',
            'submission_time': time.time(),
            'votes': {},
            'vote_count': 0,
            'vote_threshold': 0.66,
            'voting_period': 86400,
            'finalized': False
        }
        
        self.funding_proposals.append(proposal)
        return proposal
    
    def vote_on_proposal(self, proposal_id: str, voter_address: str, 
                        vote: str, voting_power: float) -> bool:
        """
        Vote on a funding proposal.
        
        Args:
            proposal_id: Proposal ID
            voter_address: Voter address
            vote: Vote type (approve/reject)
            voting_power: Voter's voting power
            
        Returns:
            True if vote was successfully recorded
        """
        proposal = self._get_proposal(proposal_id)
        
        if not proposal or proposal['status'] != 'pending':
            return False
            
        # Check if voting period has ended
        if time.time() - proposal['submission_time'] > proposal['voting_period']:
            self._finalize_proposal(proposal_id)
            return False
            
        # Check if voter has already voted
        if voter_address in proposal['votes']:
            return False
            
        proposal['votes'][voter_address] = {
            'vote': vote,
            'voting_power': voting_power,
            'timestamp': time.time()
        }
        proposal['vote_count'] += 1
        
        # Check if vote threshold is met
        if self._has_reached_threshold(proposal):
            self._finalize_proposal(proposal_id)
            
        return True
    
    def _has_reached_threshold(self, proposal: Dict) -> bool:
        """Check if proposal has reached vote threshold."""
        total_power = sum(vote['voting_power'] for vote in proposal['votes'].values())
        approval_power = sum(vote['voting_power'] for vote in proposal['votes'].values() 
                          if vote['vote'] == 'approve')
        
        if total_power == 0:
            return False
            
        return (approval_power / total_power) >= proposal['vote_threshold']
    
    def _finalize_proposal(self, proposal_id: str):
        """Finalize a proposal based on votes."""
        proposal = self._get_proposal(proposal_id)
        
        if not proposal or proposal['finalized']:
            return
            
        proposal['finalized'] = True
        
        # Determine outcome
        if self._has_reached_threshold(proposal):
            proposal['status'] = 'approved'
            self.approved_proposals.append(proposal)
            self.funding_proposals.remove(proposal)
            
            # Execute payment
            self._execute_payment(proposal)
        else:
            proposal['status'] = 'rejected'
            self.rejected_proposals.append(proposal)
            self.funding_proposals.remove(proposal)
    
    def _execute_payment(self, proposal: Dict):
        """Execute payment for approved proposal."""
        if self.balance < proposal['amount'] + proposal['fee']:
            proposal['status'] = 'failed'
            return False
            
        # Transfer funds
        self.balance -= proposal['amount']
        
        # Add transaction record
        transaction = {
            'transaction_id': self._generate_transaction_id(),
            'type': 'funding',
            'from_address': self.treasury_address,
            'to_address': proposal['recipient_address'],
            'amount': proposal['amount'],
            'fee': proposal['fee'],
            'timestamp': time.time(),
            'proposal_id': proposal['proposal_id']
        }
        
        self.transactions.append(transaction)
        return True
    
    def add_funds(self, from_address: str, amount: float) -> bool:
        """
        Add funds to treasury.
        
        Args:
            from_address: Sender address
            amount: Amount to add
            
        Returns:
            True if funds were successfully added
        """
        if amount <= 0:
            return False
            
        self.balance += amount
        
        transaction = {
            'transaction_id': self._generate_transaction_id(),
            'type': 'deposit',
            'from_address': from_address,
            'to_address': self.treasury_address,
            'amount': amount,
            'fee': 0,
            'timestamp': time.time(),
            'proposal_id': None
        }
        
        self.transactions.append(transaction)
        return True
    
    def transfer_funds(self, to_address: str, amount: float) -> bool:
        """
        Transfer funds from treasury.
        
        Args:
            to_address: Recipient address
            amount: Amount to transfer
            
        Returns:
            True if transfer was successful
        """
        if amount <= 0 or self.balance < amount:
            return False
            
        self.balance -= amount
        
        transaction = {
            'transaction_id': self._generate_transaction_id(),
            'type': 'transfer',
            'from_address': self.treasury_address,
            'to_address': to_address,
            'amount': amount,
            'fee': 0,
            'timestamp': time.time(),
            'proposal_id': None
        }
        
        self.transactions.append(transaction)
        return True
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """
        Get proposal by ID.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal dictionary if found, None otherwise
        """
        return self._get_proposal(proposal_id)
    
    def get_proposals(self, status: str = None) -> List[Dict]:
        """
        Get all proposals.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of proposals
        """
        if status:
            if status == 'pending':
                return self.funding_proposals
            elif status == 'approved':
                return self.approved_proposals
            elif status == 'rejected':
                return self.rejected_proposals
            else:
                return []
                
        return (self.funding_proposals + 
                self.approved_proposals + 
                self.rejected_proposals)
    
    def get_transactions(self, transaction_type: str = None) -> List[Dict]:
        """
        Get treasury transactions.
        
        Args:
            transaction_type: Optional transaction type filter
            
        Returns:
            List of transactions
        """
        if transaction_type:
            return [tx for tx in self.transactions if tx['type'] == transaction_type]
            
        return self.transactions
    
    def get_treasury_info(self) -> Dict:
        """
        Get treasury information.
        
        Returns:
            Treasury information dictionary
        """
        proposal_stats = {
            'pending': len(self.funding_proposals),
            'approved': len(self.approved_proposals),
            'rejected': len(self.rejected_proposals),
            'total': len(self.funding_proposals) + len(self.approved_proposals) + len(self.rejected_proposals)
        }
        
        transaction_stats = {
            'deposits': len([tx for tx in self.transactions if tx['type'] == 'deposit']),
            'withdrawals': len([tx for tx in self.transactions if tx['type'] == 'transfer']),
            'funding': len([tx for tx in self.transactions if tx['type'] == 'funding']),
            'total': len(self.transactions)
        }
        
        return {
            'treasury_address': self.treasury_address,
            'balance': self.balance,
            'proposal_stats': proposal_stats,
            'transaction_stats': transaction_stats
        }
    
    def get_funding_stats(self) -> Dict:
        """
        Get funding statistics.
        
        Returns:
            Funding statistics dictionary
        """
        total_requested = sum(p['amount'] for p in self.funding_proposals)
        total_approved = sum(p['amount'] for p in self.approved_proposals)
        total_rejected = sum(p['amount'] for p in self.rejected_proposals)
        
        return {
            'total_requested': total_requested,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'average_proposal_amount': total_requested / len(self.funding_proposals) if self.funding_proposals else 0,
            'funding_success_rate': (total_approved / (total_approved + total_rejected)) * 100 if (total_approved + total_rejected) > 0 else 0
        }
    
    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        return sha256_hash(f"{self.dao.dao_id}:proposal:{time.time()}")[:16]
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        self.transaction_counter += 1
        return sha256_hash(f"{self.treasury_address}:{self.transaction_counter}:{time.time()}")[:24]
    
    def _get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Internal method to get proposal from all proposal lists."""
        for proposal in self.funding_proposals:
            if proposal['proposal_id'] == proposal_id:
                return proposal
                
        for proposal in self.approved_proposals:
            if proposal['proposal_id'] == proposal_id:
                return proposal
                
        for proposal in self.rejected_proposals:
            if proposal['proposal_id'] == proposal_id:
                return proposal
                
        return None
    
    def set_proposal_fee(self, fee_percentage: float):
        """
        Set proposal fee percentage.
        
        Args:
            fee_percentage: New fee percentage (0.0 to 1.0)
            
        Raises:
            ValueError: If fee percentage is invalid
        """
        if fee_percentage < 0 or fee_percentage > 1:
            raise ValueError("Fee percentage must be between 0 and 1")
            
        self.proposal_fee = fee_percentage
    
    def set_minimum_proposal_amount(self, amount: float):
        """
        Set minimum proposal amount.
        
        Args:
            amount: New minimum proposal amount
            
        Raises:
            ValueError: If amount is invalid
        """
        if amount <= 0:
            raise ValueError("Minimum proposal amount must be positive")
            
        self.minimum_proposal_amount = amount
    
    def set_voting_period(self, period: int):
        """
        Set voting period in seconds.
        
        Args:
            period: New voting period in seconds
            
        Raises:
            ValueError: If period is invalid
        """
        if period <= 0:
            raise ValueError("Voting period must be positive")
            
        for proposal in self.funding_proposals:
            proposal['voting_period'] = period
    
    def __repr__(self):
        """String representation of the TreasuryManager."""
        info = self.get_treasury_info()
        return (f"TreasuryManager(balance={info['balance']}, "
                f"proposals={info['proposal_stats']['total']}, "
                f"transactions={info['transaction_stats']['total']})")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_treasury_info()
        funding_stats = self.get_funding_stats()
        
        return (
            f"ChainForge Treasury\n"
            f"==================\n"
            f"Address: {self.treasury_address}\n"
            f"Balance: {info['balance']}\n"
            f"Proposals: {info['proposal_stats']['pending']} pending, "
            f"{info['proposal_stats']['approved']} approved, "
            f"{info['proposal_stats']['rejected']} rejected\n"
            f"Transactions: {info['transaction_stats']['total']} total\n"
            f"Total Requested: {funding_stats['total_requested']}\n"
            f"Total Approved: {funding_stats['total_approved']}\n"
            f"Success Rate: {funding_stats['funding_success_rate']:.1f}%"
        )
