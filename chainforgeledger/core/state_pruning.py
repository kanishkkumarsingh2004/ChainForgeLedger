"""
ChainForgeLedger State Pruning

Implements state pruning mechanism for blockchain storage optimization.
"""

import time
import os
import json
from typing import Dict, List
from chainforgeledger.tokenomics.treasury import TreasuryManager


class StatePruner:
    """
    Blockchain state pruning for storage optimization.
    
    Attributes:
        storage_dir: Directory where blockchain state is stored
        pruning_policy: Pruning policy configuration
        pruning_history: History of pruning operations
        state_size: Current blockchain state size in bytes
        storage_limit: Maximum storage limit to enforce pruning
        block_retention: Number of recent blocks to retain in full state
        snapshot_interval: Interval at which to take state snapshots
        last_pruning_time: Last pruning operation time
        last_snapshot_time: Last snapshot time
    """
    
    DEFAULT_PRUNING_POLICY = {
        'enabled': True,
        'block_retention': 10000,
        'snapshot_interval': 5000,
        'storage_limit': 10 * 1024 * 1024 * 1024,  # 10GB
        'pruning_batch_size': 1000,
        'compression_enabled': True,
        'compression_level': 6
    }
    
    def __init__(self, storage_dir: str,
                 treasury: TreasuryManager,
                 pruning_policy: Dict = None):
        """
        Initialize a StatePruner instance.
        
        Args:
            storage_dir: Blockchain storage directory
            treasury: Treasury manager
            pruning_policy: Optional pruning policy configuration
        """
        self.storage_dir = storage_dir
        self.treasury = treasury
        self.pruning_policy = pruning_policy or self.DEFAULT_PRUNING_POLICY.copy()
        self.pruning_history: List[Dict] = []
        self.state_size = self._calculate_state_size()
        self.last_pruning_time = 0
        self.last_snapshot_time = 0
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        self.snapshot_dir = os.path.join(storage_dir, 'snapshots')
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        # Load existing snapshot and pruning history
        self._load_history()
    
    def _calculate_state_size(self) -> int:
        """Calculate current state size in bytes."""
        state_size = 0
        
        for dirpath, dirnames, filenames in os.walk(self.storage_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                state_size += os.path.getsize(file_path)
                
        return state_size
    
    def _load_history(self):
        """Load pruning and snapshot history from storage."""
        history_file = os.path.join(self.snapshot_dir, 'pruning_history.json')
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.pruning_history = json.load(f)
            except Exception as e:
                print(f"Failed to load pruning history: {e}")
                
        # Load last snapshot time from metadata
        self._update_last_snapshot_time()
    
    def _update_last_snapshot_time(self):
        """Update last snapshot time from available snapshots."""
        snapshot_files = self._get_snapshot_files()
        
        if snapshot_files:
            # Sort by block number descending
            snapshot_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]), reverse=True)
            last_snapshot = snapshot_files[0]
            self.last_snapshot_time = os.path.getmtime(last_snapshot)
    
    def _get_snapshot_files(self) -> List[str]:
        """Get list of snapshot files."""
        if not os.path.exists(self.snapshot_dir):
            return []
            
        snapshot_files = []
        
        for filename in os.listdir(self.snapshot_dir):
            if filename.endswith('.snapshot'):
                snapshot_files.append(os.path.join(self.snapshot_dir, filename))
                
        return snapshot_files
    
    def is_pruning_needed(self) -> bool:
        """
        Check if pruning is needed based on current state size.
        
        Returns:
            True if pruning is needed
        """
        if not self.pruning_policy['enabled']:
            return False
            
        if self.state_size > self.pruning_policy['storage_limit']:
            return True
            
        return False
    
    def can_take_snapshot(self) -> bool:
        """
        Check if snapshot can be taken based on snapshot interval.
        
        Returns:
            True if snapshot can be taken
        """
        if not self.pruning_policy['enabled']:
            return False
            
        time_since_snapshot = time.time() - self.last_snapshot_time
        
        if time_since_snapshot > self.pruning_policy['snapshot_interval']:
            return True
            
        return False
    
    def take_snapshot(self, block_height: int) -> str:
        """
        Take a state snapshot.
        
        Args:
            block_height: Current block height
            
        Returns:
            Snapshot file path
        """
        snapshot_filename = f'state_snapshot_{block_height}.snapshot'
        snapshot_path = os.path.join(self.snapshot_dir, snapshot_filename)
        
        try:
            # In real implementation, this would serialize the current state
            self._serialize_state(snapshot_path, block_height)
            
            # Update snapshot time
            self.last_snapshot_time = time.time()
            
            # Record snapshot in history
            self.pruning_history.append({
                'type': 'snapshot',
                'block_height': block_height,
                'timestamp': time.time(),
                'size': os.path.getsize(snapshot_path),
                'file_path': snapshot_path
            })
            
            self._save_history()
            
            print(f"Snapshot taken successfully at block {block_height}: {snapshot_path}")
            return snapshot_path
            
        except Exception as e:
            print(f"Failed to take snapshot: {e}")
            return None
    
    def _serialize_state(self, file_path: str, block_height: int):
        """Serialize blockchain state to snapshot file."""
        # In real implementation, this would serialize the complete state
        state_data = {
            'snapshot_version': 1,
            'block_height': block_height,
            'timestamp': time.time(),
            'state_summary': {
                'total_blocks': block_height + 1,
                'total_transactions': 0,
                'active_accounts': 0,
                'total_balance': self.treasury.get_balance(),
                'contract_count': 0
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def prune_state(self, target_height: int = None) -> Dict:
        """
        Prune blockchain state.
        
        Args:
            target_height: Target block height to retain (default: block_retention policy)
            
        Returns:
            Pruning result information
        """
        if not self.pruning_policy['enabled']:
            return {'success': False, 'reason': 'Pruning is disabled'}
            
        if target_height is None:
            target_height = self._get_current_block_height() - self.pruning_policy['block_retention']
            
            if target_height <= 0:
                return {'success': False, 'reason': 'Not enough blocks to prune'}
                
        start_time = time.time()
        initial_size = self.state_size
        
        try:
            # Prune historical blocks
            blocks_pruned = self._prune_blocks(target_height)
            
            # Prune transaction history
            transactions_pruned = self._prune_transactions(target_height)
            
            # Prune historical state data
            state_pruned = self._prune_state_data(target_height)
            
            # Update state size
            self.state_size = self._calculate_state_size()
            
            # Record pruning operation
            self.pruning_history.append({
                'type': 'pruning',
                'target_height': target_height,
                'blocks_pruned': blocks_pruned,
                'transactions_pruned': transactions_pruned,
                'state_pruned': state_pruned,
                'initial_size': initial_size,
                'final_size': self.state_size,
                'size_reduction': initial_size - self.state_size,
                'duration': time.time() - start_time,
                'timestamp': time.time()
            })
            
            self.last_pruning_time = time.time()
            self._save_history()
            
            return {
                'success': True,
                'target_height': target_height,
                'blocks_pruned': blocks_pruned,
                'transactions_pruned': transactions_pruned,
                'state_pruned': state_pruned,
                'size_reduction': initial_size - self.state_size,
                'initial_size': initial_size,
                'final_size': self.state_size,
                'size_reduction_percentage': ((initial_size - self.state_size) / initial_size) * 100,
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            print(f"Pruning failed: {e}")
            return {'success': False, 'reason': str(e)}
    
    def _prune_blocks(self, target_height: int) -> int:
        """Prune historical block data beyond target height."""
        # In real implementation, this would delete old block files
        return 0
    
    def _prune_transactions(self, target_height: int) -> int:
        """Prune transaction history beyond target height."""
        # In real implementation, this would delete old transaction records
        return 0
    
    def _prune_state_data(self, target_height: int) -> int:
        """Prune historical state data beyond target height."""
        # In real implementation, this would delete old state data
        return 0
    
    def _get_current_block_height(self) -> int:
        """Get current blockchain height."""
        # In real implementation, this would query the blockchain
        return 0
    
    def _save_history(self):
        """Save pruning history to storage."""
        history_file = os.path.join(self.snapshot_dir, 'pruning_history.json')
        
        try:
            with open(history_file, 'w') as f:
                json.dump(self.pruning_history, f, indent=2)
        except Exception as e:
            print(f"Failed to save pruning history: {e}")
    
    def get_snapshot_info(self) -> List[Dict]:
        """
        Get snapshot information.
        
        Returns:
            List of snapshot information dictionaries
        """
        snapshot_files = self._get_snapshot_files()
        snapshots = []
        
        for file_path in snapshot_files:
            try:
                with open(file_path, 'r') as f:
                    snapshot_data = json.load(f)
                    
                snapshots.append({
                    'block_height': snapshot_data['block_height'],
                    'timestamp': snapshot_data['timestamp'],
                    'size': os.path.getsize(file_path),
                    'file_path': file_path,
                    'version': snapshot_data['snapshot_version']
                })
            except Exception as e:
                print(f"Failed to read snapshot {file_path}: {e}")
                
        # Sort by block height descending
        return sorted(snapshots, key=lambda x: x['block_height'], reverse=True)
    
    def get_pruning_info(self) -> Dict:
        """
        Get pruning information.
        
        Returns:
            Pruning information dictionary
        """
        current_block_height = self._get_current_block_height()
        eligible_height = max(0, current_block_height - self.pruning_policy['block_retention'])
        
        snapshots = self.get_snapshot_info()
        latest_snapshot = snapshots[0] if snapshots else None
        
        return {
            'enabled': self.pruning_policy['enabled'],
            'current_state_size': self.state_size,
            'storage_limit': self.pruning_policy['storage_limit'],
            'storage_used_percentage': (self.state_size / self.pruning_policy['storage_limit']) * 100,
            'pruning_needed': self.is_pruning_needed(),
            'current_block_height': current_block_height,
            'eligible_pruning_height': eligible_height,
            'block_retention': self.pruning_policy['block_retention'],
            'snapshot_interval': self.pruning_policy['snapshot_interval'],
            'compression_enabled': self.pruning_policy['compression_enabled'],
            'compression_level': self.pruning_policy['compression_level'],
            'snapshot_count': len(snapshots),
            'latest_snapshot': latest_snapshot,
            'last_pruning_time': self.last_pruning_time,
            'last_snapshot_time': self.last_snapshot_time
        }
    
    def get_pruning_history(self, limit: int = 50) -> List[Dict]:
        """
        Get pruning history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of pruning operation records
        """
        return sorted(
            self.pruning_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
    
    def get_pruning_stats(self) -> Dict:
        """
        Get pruning statistics.
        
        Returns:
            Pruning statistics dictionary
        """
        pruning_operations = [
            op for op in self.pruning_history if op['type'] == 'pruning'
        ]
        
        snapshots = [
            op for op in self.pruning_history if op['type'] == 'snapshot'
        ]
        
        total_size_reduction = sum(op['size_reduction'] for op in pruning_operations)
        avg_size_reduction = total_size_reduction / len(pruning_operations) \
                          if pruning_operations else 0
        
        total_blocks_pruned = sum(op['blocks_pruned'] for op in pruning_operations)
        avg_blocks_pruned = total_blocks_pruned / len(pruning_operations) \
                          if pruning_operations else 0
        
        avg_duration = sum(op['duration'] for op in pruning_operations) / len(pruning_operations) \
                     if pruning_operations else 0
        
        return {
            'total_pruning_operations': len(pruning_operations),
            'total_snapshots': len(snapshots),
            'total_size_reduction': total_size_reduction,
            'avg_size_reduction': avg_size_reduction,
            'total_blocks_pruned': total_blocks_pruned,
            'avg_blocks_pruned': avg_blocks_pruned,
            'avg_duration': avg_duration,
            'last_pruning_time': self.last_pruning_time
        }
    
    def set_pruning_policy(self, policy: Dict):
        """
        Set pruning policy.
        
        Args:
            policy: Pruning policy configuration
        """
        valid_keys = list(self.DEFAULT_PRUNING_POLICY.keys())
        
        for key, value in policy.items():
            if key in valid_keys:
                self.pruning_policy[key] = value
    
    def disable_pruning(self):
        """Disable pruning."""
        self.pruning_policy['enabled'] = False
    
    def enable_pruning(self):
        """Enable pruning."""
        self.pruning_policy['enabled'] = True
    
    def clean_old_snapshots(self, keep_count: int = 3):
        """
        Clean up old snapshots, keeping only the specified number.
        
        Args:
            keep_count: Number of recent snapshots to keep
        """
        snapshots = self.get_snapshot_info()
        
        if len(snapshots) <= keep_count:
            return
            
        # Keep most recent snapshots
        snapshots_to_keep = sorted(
            snapshots,
            key=lambda x: x['block_height'],
            reverse=True
        )[:keep_count]
        
        snapshots_to_delete = [
            snap for snap in snapshots 
            if snap['block_height'] < snapshots_to_keep[-1]['block_height']
        ]
        
        for snap in snapshots_to_delete:
            try:
                os.remove(snap['file_path'])
                print(f"Deleted old snapshot: {snap['file_path']}")
            except Exception as e:
                print(f"Failed to delete snapshot {snap['file_path']}: {e}")
    
    def __repr__(self):
        """String representation of the StatePruner."""
        info = self.get_pruning_info()
        return (f"StatePruner(usage={info['storage_used_percentage']:.1f}%, "
                f"pruning_needed={info['pruning_needed']})")
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_pruning_info()
        stats = self.get_pruning_stats()
        snapshots = self.get_snapshot_info()
        
        snapshot_info = "\n".join([
            f"  Block {s['block_height']}: {s['size']} bytes" 
            for s in snapshots[:3]
        ])
        
        return (
            f"State Pruner\n"
            f"============\n"
            f"Status: {'Enabled' if info['enabled'] else 'Disabled'}\n"
            f"Storage Used: {info['current_state_size'] / (1024*1024*1024):.2f}GB / "
            f"{info['storage_limit'] / (1024*1024*1024):.0f}GB "
            f"({info['storage_used_percentage']:.1f}%)\n"
            f"Pruning Needed: {'Yes' if info['pruning_needed'] else 'No'}\n"
            f"Block Retention: {info['block_retention']} blocks\n"
            f"Snapshot Interval: {info['snapshot_interval']} blocks\n"
            f"Compression: {'Level ' + str(info['compression_level']) if info['compression_enabled'] else 'Disabled'}\n"
            f"Current Height: {info['current_block_height']}\n"
            f"Latest Snapshot: Block {info['latest_snapshot']['block_height']} "
            f"({time.ctime(info['latest_snapshot']['timestamp'])})\n"
            f"\nStatistics:\n"
            f"Total Pruning Operations: {stats['total_pruning_operations']}\n"
            f"Total Snapshots: {stats['total_snapshots']}\n"
            f"Total Size Reduction: {stats['total_size_reduction'] / (1024*1024):.2f} MB\n"
            f"Average Size Reduction: {stats['avg_size_reduction'] / (1024*1024):.2f} MB\n"
            f"Average Blocks Pruned: {stats['avg_blocks_pruned']:.0f}\n"
            f"Average Duration: {stats['avg_duration']:.2f} seconds"
        )
