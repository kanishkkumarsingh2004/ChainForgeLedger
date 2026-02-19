"""
ChainForgeLedger Cross-Chain Bridge

Implements cross-chain communication and asset transfer functionality.
"""

import time
from typing import Dict, List, Optional
from chainforgeledger.crypto.hashing import sha256_hash
from chainforgeledger.crypto.signature import Signature


class CrossChainBridge:
    """
    Cross-chain bridge implementation for asset transfers between blockchains.
    
    Attributes:
        bridge_id: Unique bridge identifier
        source_chain: Source blockchain identifier
        destination_chain: Destination blockchain identifier
        bridge_contract_address: Bridge contract address on source chain
        counterpart_contract_address: Bridge contract address on destination chain
        relayers: List of approved relayers
        relayer_threshold: Number of relayer signatures required
        pending_transfers: Dictionary of pending transfers
        completed_transfers: Dictionary of completed transfers
        failed_transfers: List of failed transfers
        fee_per_transfer: Fixed bridge fee
        min_transfer_amount: Minimum transfer amount
        max_transfer_amount: Maximum transfer amount
        transfer_timeout: Transfer timeout period
        transfer_history: Complete transfer history
    """
    
    def __init__(self, source_chain: str, destination_chain: str,
                 relayer_threshold: int = 2,
                 fee_per_transfer: int = 0,
                 min_transfer_amount: int = 1,
                 max_transfer_amount: int = 10000,
                 transfer_timeout: int = 86400):
        """
        Initialize a CrossChainBridge instance.
        
        Args:
            source_chain: Source blockchain identifier
            destination_chain: Destination blockchain identifier
            relayer_threshold: Number of relayer signatures required
            fee_per_transfer: Fixed bridge fee
            min_transfer_amount: Minimum transfer amount
            max_transfer_amount: Maximum transfer amount
            transfer_timeout: Transfer timeout period
        """
        self.bridge_id = self._generate_bridge_id(source_chain, destination_chain)
        self.source_chain = source_chain
        self.destination_chain = destination_chain
        self.bridge_contract_address = None
        self.counterpart_contract_address = None
        self.relayers: List[str] = []
        self.relayer_threshold = relayer_threshold
        self.pending_transfers: Dict[str, Dict] = {}
        self.completed_transfers: Dict[str, Dict] = {}
        self.failed_transfers: List[Dict] = []
        self.fee_per_transfer = fee_per_transfer
        self.min_transfer_amount = min_transfer_amount
        self.max_transfer_amount = max_transfer_amount
        self.transfer_timeout = transfer_timeout
        self.transfer_history: List[Dict] = []
    
    def _generate_bridge_id(self, source: str, destination: str) -> str:
        """Generate unique bridge identifier."""
        return sha256_hash(f"bridge:{source}:{destination}:{time.time()}")[:16]
    
    def add_relayer(self, relayer_address: str):
        """
        Add a relayer to the bridge.
        
        Args:
            relayer_address: Relayer address
        """
        if relayer_address not in self.relayers:
            self.relayers.append(relayer_address)
    
    def remove_relayer(self, relayer_address: str):
        """
        Remove a relayer from the bridge.
        
        Args:
            relayer_address: Relayer address
        """
        if relayer_address in self.relayers:
            self.relayers.remove(relayer_address)
    
    def set_bridge_contract(self, address: str):
        """
        Set bridge contract address on source chain.
        
        Args:
            address: Contract address
        """
        self.bridge_contract_address = address
    
    def set_counterpart_contract(self, address: str):
        """
        Set bridge contract address on destination chain.
        
        Args:
            address: Contract address
        """
        self.counterpart_contract_address = address
    
    def initiate_transfer(self, sender_address: str,
                         recipient_address: str,
                         amount: int,
                         token: str = "native") -> str:
        """
        Initiate a cross-chain transfer.
        
        Args:
            sender_address: Sender address on source chain
            recipient_address: Recipient address on destination chain
            amount: Transfer amount
            token: Token type to transfer
            
        Returns:
            Transfer ID
            
        Raises:
            Exception: If transfer initiation fails
        """
        if amount < self.min_transfer_amount or amount > self.max_transfer_amount:
            raise Exception("Transfer amount out of range")
            
        if len(self.relayers) < self.relayer_threshold:
            raise Exception("Not enough relayers available")
            
        # Generate transfer ID
        transfer_id = self._generate_transfer_id(sender_address, recipient_address, amount)
        
        # Create transfer record
        transfer = {
            'transfer_id': transfer_id,
            'sender_address': sender_address,
            'recipient_address': recipient_address,
            'amount': amount,
            'token': token,
            'fee': self.fee_per_transfer,
            'status': 'initiated',
            'source_chain': self.source_chain,
            'destination_chain': self.destination_chain,
            'initiation_time': time.time(),
            'relayer_confirmations': [],
            'completion_time': None,
            'failure_reason': None
        }
        
        self.pending_transfers[transfer_id] = transfer
        self.transfer_history.append(transfer)
        
        return transfer_id
    
    def confirm_transfer(self, relayer_address: str,
                       transfer_id: str,
                       signature: str) -> bool:
        """
        Confirm a transfer by a relayer.
        
        Args:
            relayer_address: Relayer address
            transfer_id: Transfer ID
            signature: Relayer's signature
            
        Returns:
            True if confirmation was successful
            
        Raises:
            Exception: If confirmation fails
        """
        if transfer_id not in self.pending_transfers:
            raise Exception("Transfer not found")
            
        if relayer_address not in self.relayers:
            raise Exception("Not an authorized relayer")
            
        transfer = self.pending_transfers[transfer_id]
        
        if relayer_address in [c['relayer_address'] for c in transfer['relayer_confirmations']]:
            raise Exception("Relayer has already confirmed")
            
        # Verify signature
        if not self._verify_relayer_signature(relayer_address, transfer_id, signature):
            raise Exception("Invalid signature")
            
        # Add relayer confirmation
        transfer['relayer_confirmations'].append({
            'relayer_address': relayer_address,
            'signature': signature,
            'timestamp': time.time()
        })
        
        # Check if transfer has enough confirmations
        if len(transfer['relayer_confirmations']) >= self.relayer_threshold:
            self._complete_transfer(transfer_id)
            
        return True
    
    def _verify_relayer_signature(self, relayer_address: str,
                                  transfer_id: str,
                                  signature: str) -> bool:
        """
        Verify relayer signature for transfer confirmation.
        
        Args:
            relayer_address: Relayer address
            transfer_id: Transfer ID
            signature: Signature to verify
            
        Returns:
            True if signature is valid
        """
        # In a real implementation, this would verify against relayer's public key
        return Signature.verify(f"{transfer_id}:{relayer_address}", signature, relayer_address)
    
    def _complete_transfer(self, transfer_id: str):
        """Complete a transfer with sufficient confirmations."""
        transfer = self.pending_transfers[transfer_id]
        transfer['status'] = 'completed'
        transfer['completion_time'] = time.time()
        
        # Move from pending to completed
        del self.pending_transfers[transfer_id]
        self.completed_transfers[transfer_id] = transfer
    
    def fail_transfer(self, transfer_id: str, reason: str):
        """
        Mark a transfer as failed.
        
        Args:
            transfer_id: Transfer ID
            reason: Failure reason
        """
        if transfer_id in self.pending_transfers:
            transfer = self.pending_transfers[transfer_id]
            transfer['status'] = 'failed'
            transfer['failure_reason'] = reason
            transfer['completion_time'] = time.time()
            
            self.failed_transfers.append(transfer)
            del self.pending_transfers[transfer_id]
        elif transfer_id in self.transfer_history:
            transfer = next(t for t in self.transfer_history if t['transfer_id'] == transfer_id)
            transfer['status'] = 'failed'
            transfer['failure_reason'] = reason
            transfer['completion_time'] = time.time()
            
            self.failed_transfers.append(transfer)
    
    def process_transfer_timeout(self):
        """Process transfers that have timed out."""
        current_time = time.time()
        transfers_to_timeout = []
        
        for transfer_id, transfer in self.pending_transfers.items():
            if current_time - transfer['initiation_time'] > self.transfer_timeout:
                transfers_to_timeout.append(transfer_id)
                
        for transfer_id in transfers_to_timeout:
            self.fail_transfer(transfer_id, "Transfer timed out")
    
    def _generate_transfer_id(self, sender: str, recipient: str, amount: int) -> str:
        """Generate unique transfer identifier."""
        return sha256_hash(f"{sender}:{recipient}:{amount}:{time.time()}")[:24]
    
    def get_transfer_status(self, transfer_id: str) -> Dict:
        """
        Get transfer status.
        
        Args:
            transfer_id: Transfer ID
            
        Returns:
            Transfer status information
        """
        if transfer_id in self.pending_transfers:
            transfer = self.pending_transfers[transfer_id]
        elif transfer_id in self.completed_transfers:
            transfer = self.completed_transfers[transfer_id]
        else:
            transfer = next((t for t in self.failed_transfers if t['transfer_id'] == transfer_id), None)
            
        if transfer is None:
            raise Exception("Transfer not found")
            
        return {
            'transfer_id': transfer['transfer_id'],
            'status': transfer['status'],
            'sender_address': transfer['sender_address'],
            'recipient_address': transfer['recipient_address'],
            'amount': transfer['amount'],
            'token': transfer['token'],
            'fee': transfer['fee'],
            'initiation_time': transfer['initiation_time'],
            'completion_time': transfer['completion_time'],
            'relayer_confirmations': len(transfer['relayer_confirmations']),
            'relayer_threshold': self.relayer_threshold,
            'failure_reason': transfer.get('failure_reason', None)
        }
    
    def get_transfer_history(self, sender_address: str = None,
                            recipient_address: str = None,
                            start_time: float = None,
                            end_time: float = None,
                            status: str = None) -> List[Dict]:
        """
        Get transfer history.
        
        Args:
            sender_address: Optional sender address filter
            recipient_address: Optional recipient address filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            status: Optional status filter
            
        Returns:
            List of transfer records
        """
        transfers = self.transfer_history.copy()
        
        if sender_address:
            transfers = [t for t in transfers if t['sender_address'] == sender_address]
            
        if recipient_address:
            transfers = [t for t in transfers if t['recipient_address'] == recipient_address]
            
        if start_time:
            transfers = [t for t in transfers if t['initiation_time'] >= start_time]
            
        if end_time:
            transfers = [t for t in transfers if t['initiation_time'] <= end_time]
            
        if status:
            transfers = [t for t in transfers if t['status'] == status]
            
        return sorted(transfers, key=lambda x: x['initiation_time'], reverse=True)
    
    def get_bridge_info(self) -> Dict:
        """
        Get bridge information.
        
        Returns:
            Bridge information dictionary
        """
        return {
            'bridge_id': self.bridge_id,
            'source_chain': self.source_chain,
            'destination_chain': self.destination_chain,
            'bridge_contract_address': self.bridge_contract_address,
            'counterpart_contract_address': self.counterpart_contract_address,
            'relayer_count': len(self.relayers),
            'relayer_threshold': self.relayer_threshold,
            'fee_per_transfer': self.fee_per_transfer,
            'min_transfer_amount': self.min_transfer_amount,
            'max_transfer_amount': self.max_transfer_amount,
            'transfer_timeout': self.transfer_timeout,
            'pending_transfers': len(self.pending_transfers),
            'completed_transfers': len(self.completed_transfers),
            'failed_transfers': len(self.failed_transfers)
        }
    
    def get_bridge_stats(self) -> Dict:
        """
        Get bridge statistics.
        
        Returns:
            Bridge statistics dictionary
        """
        total_transfers = len(self.transfer_history)
        completed_transfers = len(self.completed_transfers)
        pending_transfers = len(self.pending_transfers)
        failed_transfers = len(self.failed_transfers)
        
        total_amount = sum(t['amount'] for t in self.transfer_history)
        completed_amount = sum(t['amount'] for t in self.completed_transfers.values())
        total_fees = sum(t['fee'] for t in self.transfer_history)
        
        success_rate = (completed_transfers / total_transfers) * 100 if total_transfers > 0 else 0
        
        avg_transfer_time = 0
        if completed_transfers > 0:
            transfer_times = [t['completion_time'] - t['initiation_time'] 
                           for t in self.completed_transfers.values()]
            avg_transfer_time = sum(transfer_times) / completed_transfers
        
        return {
            'total_transfers': total_transfers,
            'completed_transfers': completed_transfers,
            'pending_transfers': pending_transfers,
            'failed_transfers': failed_transfers,
            'success_rate': success_rate,
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'total_fees': total_fees,
            'avg_transfer_amount': total_amount / total_transfers if total_transfers > 0 else 0,
            'avg_transfer_time': avg_transfer_time,
            'transfer_throughput': total_transfers / 30  # Last 30 days
        }
    
    def set_fee_per_transfer(self, fee: int):
        """
        Set fee per transfer.
        
        Args:
            fee: New fee amount
            
        Raises:
            Exception: If fee is invalid
        """
        if fee < 0:
            raise Exception("Fee must be non-negative")
            
        self.fee_per_transfer = fee
    
    def set_transfer_limits(self, min_amount: int, max_amount: int):
        """
        Set transfer limits.
        
        Args:
            min_amount: Minimum transfer amount
            max_amount: Maximum transfer amount
            
        Raises:
            Exception: If limits are invalid
        """
        if min_amount <= 0 or max_amount < min_amount:
            raise Exception("Invalid transfer limits")
            
        self.min_transfer_amount = min_amount
        self.max_transfer_amount = max_amount
    
    def set_relayer_threshold(self, threshold: int):
        """
        Set relayer threshold.
        
        Args:
            threshold: Number of signatures required
            
        Raises:
            Exception: If threshold is invalid
        """
        if threshold < 1 or threshold > len(self.relayers):
            raise Exception("Invalid relayer threshold")
            
        self.relayer_threshold = threshold
    
    def __repr__(self):
        """String representation of the CrossChainBridge."""
        info = self.get_bridge_info()
        return (f"CrossChainBridge({self.source_chain} → {self.destination_chain}, "
                f"transfers={info['pending_transfers']} pending, "
                f"{info['completed_transfers']} completed)")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_bridge_info()
        stats = self.get_bridge_stats()
        
        return (
            f"Cross-Chain Bridge {self.bridge_id}\n"
            f"==========================\n"
            f"Chain Pair: {self.source_chain} → {self.destination_chain}\n"
            f"Bridge Contract: {self.bridge_contract_address or 'Not deployed'}\n"
            f"Counterpart Contract: {self.counterpart_contract_address or 'Not deployed'}\n"
            f"Relayers: {info['relayer_count']} (Threshold: {info['relayer_threshold']})\n"
            f"Fee: {self.fee_per_transfer}\n"
            f"Transfer Limits: {self.min_transfer_amount} - {self.max_transfer_amount}\n"
            f"Timeout: {self.transfer_timeout} seconds\n"
            f"\nStatistics:\n"
            f"Total Transfers: {stats['total_transfers']}\n"
            f"Completed: {stats['completed_transfers']} ({stats['success_rate']:.1f}%)\n"
            f"Pending: {stats['pending_transfers']}\n"
            f"Failed: {stats['failed_transfers']}\n"
            f"Total Volume: {stats['total_amount']}\n"
            f"Total Fees: {stats['total_fees']}\n"
            f"Avg Transfer Amount: {stats['avg_transfer_amount']:.2f}\n"
            f"Avg Transfer Time: {stats['avg_transfer_time']:.0f} sec"
        )


class BridgeNetwork:
    """
    Network of cross-chain bridges.
    """
    
    def __init__(self):
        """Initialize a BridgeNetwork instance."""
        self.bridges: Dict[str, CrossChainBridge] = {}
    
    def create_bridge(self, source_chain: str, destination_chain: str,
                     relayer_threshold: int = 2,
                     fee_per_transfer: int = 0,
                     min_transfer_amount: int = 1,
                     max_transfer_amount: int = 10000,
                     transfer_timeout: int = 86400) -> CrossChainBridge:
        """
        Create a new cross-chain bridge.
        
        Args:
            source_chain: Source blockchain identifier
            destination_chain: Destination blockchain identifier
            relayer_threshold: Number of relayer signatures required
            fee_per_transfer: Fixed bridge fee
            min_transfer_amount: Minimum transfer amount
            max_transfer_amount: Maximum transfer amount
            transfer_timeout: Transfer timeout period
            
        Returns:
            Created bridge instance
        """
        bridge = CrossChainBridge(source_chain, destination_chain, relayer_threshold,
                               fee_per_transfer, min_transfer_amount, max_transfer_amount,
                               transfer_timeout)
        self.bridges[bridge.bridge_id] = bridge
        return bridge
    
    def get_bridge(self, bridge_id: str) -> Optional[CrossChainBridge]:
        """
        Get bridge by ID.
        
        Args:
            bridge_id: Bridge identifier
            
        Returns:
            Bridge instance if found, None otherwise
        """
        return self.bridges.get(bridge_id)
    
    def get_bridges_by_chains(self, source_chain: str, 
                             destination_chain: str) -> List[CrossChainBridge]:
        """
        Get bridges between two chains.
        
        Args:
            source_chain: Source chain identifier
            destination_chain: Destination chain identifier
            
        Returns:
            List of bridges between specified chains
        """
        return [bridge for bridge in self.bridges.values()
               if bridge.source_chain == source_chain and 
               bridge.destination_chain == destination_chain]
    
    def get_all_bridges(self) -> List[CrossChainBridge]:
        """
        Get all bridges in the network.
        
        Returns:
            List of all bridge instances
        """
        return list(self.bridges.values())
    
    def get_network_stats(self) -> Dict:
        """
        Get network-wide bridge statistics.
        
        Returns:
            Network statistics dictionary
        """
        total_transfers = 0
        completed_transfers = 0
        total_amount = 0
        total_fees = 0
        
        for bridge in self.bridges.values():
            bridge_stats = bridge.get_bridge_stats()
            total_transfers += bridge_stats['total_transfers']
            completed_transfers += bridge_stats['completed_transfers']
            total_amount += bridge_stats['total_amount']
            total_fees += bridge_stats['total_fees']
        
        bridge_count = len(self.bridges)
        chain_pairs = set((b.source_chain, b.destination_chain) for b in self.bridges.values())
        
        return {
            'bridge_count': bridge_count,
            'chain_pairs': len(chain_pairs),
            'total_transfers': total_transfers,
            'completed_transfers': completed_transfers,
            'success_rate': (completed_transfers / total_transfers) * 100 if total_transfers > 0 else 0,
            'total_amount': total_amount,
            'total_fees': total_fees,
            'avg_transfer_amount': total_amount / total_transfers if total_transfers > 0 else 0
        }
    
    def __repr__(self):
        """String representation of the BridgeNetwork."""
        stats = self.get_network_stats()
        return (f"BridgeNetwork(bridges={stats['bridge_count']}, "
                f"chain_pairs={stats['chain_pairs']}, "
                f"transfers={stats['total_transfers']})")
