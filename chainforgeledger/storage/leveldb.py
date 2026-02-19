"""
ChainForgeLedger LevelDB Storage Module

LevelDB-compatible storage implementation for blockchain data.
"""

import os
import json
import threading
from typing import Any, Dict, List, Optional
from chainforgeledger.utils.logger import get_logger


class LevelDBStorage:
    """
    LevelDB-compatible storage implementation for blockchain.
    
    Provides a simple key-value storage interface with LevelDB-like behavior
    using file system storage.
    """
    
    def __init__(self, db_path: str = "chainforgeledger.db"):
        """
        Initialize LevelDB storage.
        
        Args:
            db_path: Database directory path
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = get_logger(__name__)
        self._ensure_directory_exists()
        self._initialize_metadata()
    
    def _ensure_directory_exists(self):
        """Ensure database directory exists."""
        try:
            if not os.path.exists(self.db_path):
                os.makedirs(self.db_path)
                self.logger.debug(f"Database directory created: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to create database directory: {e}")
            raise
    
    def _initialize_metadata(self):
        """Initialize metadata file."""
        try:
            metadata_path = os.path.join(self.db_path, "metadata.json")
            if not os.path.exists(metadata_path):
                metadata = {
                    "version": "1.0.0",
                    "created_at": self._get_current_timestamp(),
                    "last_modified": self._get_current_timestamp(),
                    "stats": {
                        "total_keys": 0,
                        "total_size": 0,
                        "block_count": 0,
                        "transaction_count": 0,
                        "contract_count": 0,
                        "wallet_count": 0
                    }
                }
                self._write_file(metadata_path, json.dumps(metadata))
                self.logger.debug("Database metadata initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize metadata: {e}")
            raise
    
    def _get_current_timestamp(self):
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)
    
    def _write_file(self, file_path: str, content: str):
        """Write content to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    def _read_file(self, file_path: str) -> str:
        """Read content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    def _get_metadata(self) -> Dict:
        """Get database metadata."""
        metadata_path = os.path.join(self.db_path, "metadata.json")
        return json.loads(self._read_file(metadata_path))
    
    def _update_metadata(self, updates: Dict):
        """Update metadata."""
        metadata = self._get_metadata()
        metadata.update(updates)
        metadata["last_modified"] = self._get_current_timestamp()
        
        metadata_path = os.path.join(self.db_path, "metadata.json")
        self._write_file(metadata_path, json.dumps(metadata))
    
    # Key-value operations
    def put(self, key: str, value: Any):
        """
        Put key-value pair into storage.
        
        Args:
            key: Key
            value: Value to store
        """
        try:
            with self.lock:
                # Validate key format
                if not key or not isinstance(key, str):
                    raise ValueError("Key must be a non-empty string")
                
                # Create directory structure if needed
                dir_path = self._get_key_directory(key)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                
                # Write value to file
                file_path = os.path.join(dir_path, self._get_key_filename(key))
                self._write_file(file_path, json.dumps(value))
                
                # Update metadata
                metadata = self._get_metadata()
                metadata["stats"]["total_keys"] += 1
                metadata["stats"]["total_size"] += os.path.getsize(file_path)
                self._update_metadata(metadata)
                
                self.logger.debug(f"Stored key '{key}'")
                
        except Exception as e:
            self.logger.error(f"Failed to put key '{key}': {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from storage.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Value or None if not found
        """
        try:
            with self.lock:
                file_path = self._get_key_file_path(key)
                if os.path.exists(file_path):
                    return json.loads(self._read_file(file_path))
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get key '{key}': {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete key from storage.
        
        Args:
            key: Key to delete
            
        Returns:
            True if key existed and was deleted, False otherwise
        """
        try:
            with self.lock:
                file_path = self._get_key_file_path(key)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    
                    # Clean up empty directories
                    self._cleanup_directory(self._get_key_directory(key))
                    
                    # Update metadata
                    metadata = self._get_metadata()
                    metadata["stats"]["total_keys"] -= 1
                    metadata["stats"]["total_size"] -= file_size
                    self._update_metadata(metadata)
                    
                    self.logger.debug(f"Deleted key '{key}'")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            with self.lock:
                return os.path.exists(self._get_key_file_path(key))
        except Exception as e:
            self.logger.error(f"Failed to check key '{key}': {e}")
            return False
    
    def keys(self, prefix: str = "") -> List[str]:
        """
        Get all keys with specified prefix.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        try:
            keys = []
            
            with self.lock:
                if prefix:
                    prefix_dir = self._get_key_directory(prefix)
                    if os.path.exists(prefix_dir):
                        keys = self._find_keys(prefix_dir, prefix)
                else:
                    # Search all directories
                    keys = self._find_keys(self.db_path, "")
                
            return keys
                
        except Exception as e:
            self.logger.error(f"Failed to get keys: {e}")
            return []
    
    def _find_keys(self, search_dir: str, prefix: str = "") -> List[str]:
        """Recursively find keys in directory structure."""
        keys = []
        
        for entry in os.scandir(search_dir):
            if entry.is_file() and entry.name.endswith('.json'):
                key = prefix + entry.name[:-5]  # Remove .json extension
                keys.append(key)
            elif entry.is_dir():
                # Recursively search subdirectories
                subkeys = self._find_keys(
                    entry.path,
                    prefix + entry.name + '/'
                )
                keys.extend(subkeys)
        
        return keys
    
    # Database operations
    def snapshot(self) -> "LevelDBStorage":
        """
        Create a snapshot of the database.
        
        Returns:
            Snapshot instance
        """
        snapshot_dir = os.path.join(self.db_path, f"snapshot_{self._get_current_timestamp()}")
        snapshot = LevelDBStorage(snapshot_dir)
        
        import shutil
        for item in os.listdir(self.db_path):
            item_path = os.path.join(self.db_path, item)
            if item != "snapshots" and os.path.isfile(item_path):
                shutil.copy2(item_path, snapshot_dir)
        
        self.logger.debug(f"Snapshot created at: {snapshot_dir}")
        return snapshot
    
    def clear(self):
        """Clear all data from database."""
        try:
            import shutil
            
            with self.lock:
                # Remove all subdirectories and files except metadata
                for item in os.listdir(self.db_path):
                    item_path = os.path.join(self.db_path, item)
                    if item != "metadata.json" and item != "snapshots":
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                
                # Reset metadata
                self._initialize_metadata()
                
                self.logger.debug("Database cleared")
                
        except Exception as e:
            self.logger.error(f"Failed to clear database: {e}")
            raise
    
    def size(self) -> int:
        """
        Get database size in bytes.
        
        Returns:
            Database size
        """
        try:
            total_size = 0
            
            with self.lock:
                for dirpath, dirnames, filenames in os.walk(self.db_path):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(file_path)
                
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to get database size: {e}")
            return 0
    
    def stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            with self.lock:
                metadata = self._get_metadata()
                return metadata.get("stats", {})
                
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {}
    
    def info(self) -> Dict:
        """
        Get database information.
        
        Returns:
            Database information
        """
        try:
            with self.lock:
                metadata = self._get_metadata()
                
                return {
                    "version": metadata.get("version"),
                    "created_at": metadata.get("created_at"),
                    "last_modified": metadata.get("last_modified"),
                    "path": self.db_path,
                    "size": self.size(),
                    "stats": self.stats(),
                    "files": self._count_files()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {}
    
    def _count_files(self) -> int:
        """Count number of files in database."""
        count = 0
        
        for dirpath, dirnames, filenames in os.walk(self.db_path):
            for filename in filenames:
                if filename != "metadata.json" and filename != "CURRENT":
                    count += 1
        
        return count
    
    # Helper methods for key management
    def _get_key_directory(self, key: str) -> str:
        """Get directory path for key."""
        parts = key.split('/')
        if len(parts) > 1:
            dir_name = parts[0]
            return os.path.join(self.db_path, dir_name)
        return self.db_path
    
    def _get_key_filename(self, key: str) -> str:
        """Get filename for key."""
        parts = key.split('/')
        filename = parts[-1]
        return f"{filename}.json"
    
    def _get_key_file_path(self, key: str) -> str:
        """Get full file path for key."""
        return os.path.join(self._get_key_directory(key), self._get_key_filename(key))
    
    def _cleanup_directory(self, dir_path: str):
        """Clean up empty directories."""
        try:
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
                
                # Check parent directory
                parent_dir = os.path.dirname(dir_path)
                if parent_dir != self.db_path and os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup directory {dir_path}: {e}")
    
    # Batch operations
    def batch(self):
        """
        Create a batch operation context manager.
        
        Returns:
            Batch operation context manager
        """
        return BatchOperation(self)
    
    # Special methods for blockchain data
    def get_block(self, block_index: int) -> Optional[Dict]:
        """
        Get block by index.
        
        Args:
            block_index: Block index
            
        Returns:
            Block data or None
        """
        key = f"blocks/block_{block_index}"
        return self.get(key)
    
    def put_block(self, block_index: int, block_data: Dict):
        """
        Put block data into storage.
        
        Args:
            block_index: Block index
            block_data: Block data
        """
        key = f"blocks/block_{block_index}"
        self.put(key, block_data)
        
        # Update block count
        metadata = self._get_metadata()
        if block_index + 1 > metadata["stats"]["block_count"]:
            metadata["stats"]["block_count"] = block_index + 1
            self._update_metadata(metadata)
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction data or None
        """
        key = f"transactions/{transaction_id}"
        return self.get(key)
    
    def put_transaction(self, transaction_id: str, transaction_data: Dict):
        """
        Put transaction data into storage.
        
        Args:
            transaction_id: Transaction ID
            transaction_data: Transaction data
        """
        key = f"transactions/{transaction_id}"
        self.put(key, transaction_data)
        
        # Update transaction count
        metadata = self._get_metadata()
        metadata["stats"]["transaction_count"] += 1
        self._update_metadata(metadata)
    
    def get_contract(self, contract_address: str) -> Optional[Dict]:
        """
        Get contract by address.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract data or None
        """
        key = f"contracts/{contract_address}"
        return self.get(key)
    
    def put_contract(self, contract_address: str, contract_data: Dict):
        """
        Put contract data into storage.
        
        Args:
            contract_address: Contract address
            contract_data: Contract data
        """
        key = f"contracts/{contract_address}"
        self.put(key, contract_data)
        
        # Update contract count
        metadata = self._get_metadata()
        metadata["stats"]["contract_count"] += 1
        self._update_metadata(metadata)
    
    def get_wallet(self, address: str) -> Optional[Dict]:
        """
        Get wallet by address.
        
        Args:
            address: Wallet address
            
        Returns:
            Wallet data or None
        """
        key = f"wallets/{address}"
        return self.get(key)
    
    def put_wallet(self, address: str, wallet_data: Dict):
        """
        Put wallet data into storage.
        
        Args:
            address: Wallet address
            wallet_data: Wallet data
        """
        key = f"wallets/{address}"
        self.put(key, wallet_data)
        
        # Update wallet count
        metadata = self._get_metadata()
        metadata["stats"]["wallet_count"] += 1
        self._update_metadata(metadata)
    
    # Context manager
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
    
    def __repr__(self):
        """String representation."""
        return f"LevelDBStorage(path={self.db_path})"
    
    def __str__(self):
        """String representation for printing."""
        try:
            info = self.info()
            
            return (
                f"ChainForgeLedger LevelDB Storage\n"
                f"=================================\n"
                f"Path: {info['path']}\n"
                f"Version: {info['version']}\n"
                f"Size: {info['size']:,} bytes\n"
                f"Blocks: {info['stats']['block_count']:,}\n"
                f"Transactions: {info['stats']['transaction_count']:,}\n"
                f"Contracts: {info['stats']['contract_count']:,}\n"
                f"Wallets: {info['stats']['wallet_count']:,}\n"
                f"Keys: {info['stats']['total_keys']:,}\n"
                f"Files: {info['files']:,}"
            )
            
        except Exception as e:
            return f"LevelDBStorage({self.db_path}) - Error: {e}"


class BatchOperation:
    """
    Batch operation context manager.
    
    Provides atomic batch operations for LevelDB storage.
    """
    
    def __init__(self, storage: LevelDBStorage):
        """
        Initialize batch operation.
        
        Args:
            storage: LevelDB storage instance
        """
        self.storage = storage
        self.operations = []
    
    def put(self, key: str, value: Any):
        """Put operation."""
        self.operations.append(('put', key, value))
    
    def delete(self, key: str):
        """Delete operation."""
        self.operations.append(('delete', key))
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            # No exception, apply changes
            self._apply()
    
    def _apply(self):
        """Apply all operations in batch."""
        with self.storage.lock:
            for op in self.operations:
                if op[0] == 'put':
                    self.storage.put(op[1], op[2])
                elif op[0] == 'delete':
                    self.storage.delete(op[1])
