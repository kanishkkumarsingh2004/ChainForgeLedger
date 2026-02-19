"""
ChainForgeLedger Block Serialization

Handles serialization and deserialization of blockchain blocks and transactions.
"""

import json
import pickle
import msgpack
from typing import List, Dict, Any
from chainforgeledger.core.block import Block
from chainforgeledger.core.transaction import Transaction


class BlockSerializer:
    """
    Handles serialization and deserialization of blockchain blocks.
    
    Supports multiple serialization formats:
    - JSON
    - Binary (pickle)
    - MessagePack (msgpack)
    """
    
    FORMATS = ['json', 'binary', 'msgpack']
    
    def __init__(self, default_format: str = 'json'):
        """
        Initialize a BlockSerializer instance.
        
        Args:
            default_format: Default serialization format
            
        Raises:
            ValueError: If format is not supported
        """
        if default_format not in self.FORMATS:
            raise ValueError(f"Unsupported format: {default_format}")
            
        self.default_format = default_format
    
    def serialize_block(self, block: Block, format: str = None) -> bytes:
        """
        Serialize a block to bytes.
        
        Args:
            block: Block to serialize
            format: Serialization format (json, binary, msgpack)
            
        Returns:
            Serialized block bytes
            
        Raises:
            ValueError: If format is not supported
        """
        format = format or self.default_format
        
        block_dict = self._block_to_dict(block)
        
        if format == 'json':
            return json.dumps(block_dict, indent=2).encode('utf-8')
        elif format == 'binary':
            return pickle.dumps(block_dict)
        elif format == 'msgpack':
            return msgpack.packb(block_dict)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def deserialize_block(self, data: bytes, format: str = None) -> Block:
        """
        Deserialize bytes to a Block instance.
        
        Args:
            data: Serialized block bytes
            format: Serialization format (json, binary, msgpack)
            
        Returns:
            Block instance
            
        Raises:
            ValueError: If format is not supported
            Exception: If deserialization fails
        """
        format = format or self.default_format
        
        try:
            if format == 'json':
                block_dict = json.loads(data.decode('utf-8'))
            elif format == 'binary':
                block_dict = pickle.loads(data)
            elif format == 'msgpack':
                block_dict = msgpack.unpackb(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            return self._dict_to_block(block_dict)
            
        except Exception as e:
            raise Exception(f"Deserialization failed: {e}")
    
    def serialize_transaction(self, transaction: Transaction, format: str = None) -> bytes:
        """
        Serialize a transaction to bytes.
        
        Args:
            transaction: Transaction to serialize
            format: Serialization format
            
        Returns:
            Serialized transaction bytes
        """
        format = format or self.default_format
        
        tx_dict = self._transaction_to_dict(transaction)
        
        if format == 'json':
            return json.dumps(tx_dict, indent=2).encode('utf-8')
        elif format == 'binary':
            return pickle.dumps(tx_dict)
        elif format == 'msgpack':
            return msgpack.packb(tx_dict)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def deserialize_transaction(self, data: bytes, format: str = None) -> Transaction:
        """
        Deserialize bytes to a Transaction instance.
        
        Args:
            data: Serialized transaction bytes
            format: Serialization format
            
        Returns:
            Transaction instance
        """
        format = format or self.default_format
        
        try:
            if format == 'json':
                tx_dict = json.loads(data.decode('utf-8'))
            elif format == 'binary':
                tx_dict = pickle.loads(data)
            elif format == 'msgpack':
                tx_dict = msgpack.unpackb(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            return self._dict_to_transaction(tx_dict)
            
        except Exception as e:
            raise Exception(f"Deserialization failed: {e}")
    
    def serialize_blockchain(self, blocks: List[Block], format: str = None) -> bytes:
        """
        Serialize entire blockchain to bytes.
        
        Args:
            blocks: List of blocks to serialize
            format: Serialization format
            
        Returns:
            Serialized blockchain bytes
        """
        format = format or self.default_format
        
        blockchain_data = {
            'version': 1,
            'block_count': len(blocks),
            'blocks': [self._block_to_dict(block) for block in blocks]
        }
        
        if format == 'json':
            return json.dumps(blockchain_data, indent=2).encode('utf-8')
        elif format == 'binary':
            return pickle.dumps(blockchain_data)
        elif format == 'msgpack':
            return msgpack.packb(blockchain_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def deserialize_blockchain(self, data: bytes, format: str = None) -> List[Block]:
        """
        Deserialize bytes to blockchain (list of blocks).
        
        Args:
            data: Serialized blockchain bytes
            format: Serialization format
            
        Returns:
            List of Block instances
        """
        format = format or self.default_format
        
        try:
            if format == 'json':
                blockchain_data = json.loads(data.decode('utf-8'))
            elif format == 'binary':
                blockchain_data = pickle.loads(data)
            elif format == 'msgpack':
                blockchain_data = msgpack.unpackb(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            return [self._dict_to_block(block_dict) 
                    for block_dict in blockchain_data.get('blocks', [])]
            
        except Exception as e:
            raise Exception(f"Deserialization failed: {e}")
    
    def _block_to_dict(self, block: Block) -> Dict[str, Any]:
        """Convert Block instance to dictionary."""
        return {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': [self._transaction_to_dict(tx) for tx in block.transactions],
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'nonce': block.nonce,
            'validator': block.validator,
            'difficulty': block.difficulty
        }
    
    def _dict_to_block(self, block_dict: Dict[str, Any]) -> Block:
        """Convert dictionary to Block instance."""
        # Create block instance
        block = Block(
            index=block_dict['index'],
            previous_hash=block_dict['previous_hash'],
            transactions=[],
            timestamp=block_dict.get('timestamp'),
            nonce=block_dict.get('nonce', 0),
            validator=block_dict.get('validator'),
            difficulty=block_dict.get('difficulty', 3)
        )
        
        # Add transactions
        block.transactions = [
            self._dict_to_transaction(tx_dict) 
            for tx_dict in block_dict.get('transactions', [])
        ]
        
        # Set hash directly (since it's already calculated)
        if 'hash' in block_dict:
            block.hash = block_dict['hash']
            
        return block
    
    def _transaction_to_dict(self, transaction: Transaction) -> Dict[str, Any]:
        """Convert Transaction instance to dictionary."""
        return {
            'txid': transaction.txid,
            'from_address': transaction.from_address,
            'to_address': transaction.to_address,
            'amount': transaction.amount,
            'timestamp': transaction.timestamp,
            'signature': transaction.signature,
            'data': transaction.data,
            'transaction_type': transaction.transaction_type,
            'fee': transaction.fee
        }
    
    def _dict_to_transaction(self, tx_dict: Dict[str, Any]) -> Transaction:
        """Convert dictionary to Transaction instance."""
        from chainforgeledger.core.transaction import Transaction
        
        return Transaction(
            from_address=tx_dict['from_address'],
            to_address=tx_dict['to_address'],
            amount=tx_dict['amount'],
            timestamp=tx_dict.get('timestamp'),
            signature=tx_dict.get('signature'),
            data=tx_dict.get('data'),
            transaction_type=tx_dict.get('transaction_type', 'transfer'),
            fee=tx_dict.get('fee', 0)
        )
    
    def validate_serialization(self, block: Block, format: str = None) -> bool:
        """
        Validate that serialization and deserialization produce identical blocks.
        
        Args:
            block: Block to validate
            format: Serialization format
            
        Returns:
            True if serialization is valid
        """
        try:
            serialized = self.serialize_block(block, format)
            deserialized = self.deserialize_block(serialized, format)
            
            # Compare important fields
            return (block.index == deserialized.index and
                    block.hash == deserialized.hash and
                    block.previous_hash == deserialized.previous_hash and
                    len(block.transactions) == len(deserialized.transactions))
                    
        except Exception as e:
            print(f"Validation failed: {e}")
            return False
    
    def get_format_info(self, format: str = None) -> Dict[str, Any]:
        """
        Get format-specific information.
        
        Args:
            format: Serialization format
            
        Returns:
            Dictionary with format details
        """
        format = format or self.default_format
        
        info = {
            'json': {
                'name': 'JSON',
                'description': 'Human-readable text format',
                'extension': '.json',
                'compression': 'low',
                'speed': 'medium'
            },
            'binary': {
                'name': 'Binary',
                'description': 'Python pickle format',
                'extension': '.bin',
                'compression': 'medium',
                'speed': 'fast'
            },
            'msgpack': {
                'name': 'MessagePack',
                'description': 'Efficient binary format',
                'extension': '.msgpack',
                'compression': 'high',
                'speed': 'fast'
            }
        }
        
        return info.get(format, {})
    
    def set_default_format(self, format: str):
        """
        Set default serialization format.
        
        Args:
            format: New default format
            
        Raises:
            ValueError: If format is not supported
        """
        if format not in self.FORMATS:
            raise ValueError(f"Unsupported format: {format}")
            
        self.default_format = format
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported formats.
        
        Returns:
            List of supported format names
        """
        return self.FORMATS.copy()
    
    def __repr__(self):
        """String representation of the BlockSerializer."""
        return f"BlockSerializer(format={self.default_format})"
    
    def __str__(self):
        """String representation for printing."""
        info = self.get_format_info()
        return (
            f"Block Serializer\n"
            f"================\n"
            f"Default Format: {info['name']}\n"
            f"Description: {info['description']}\n"
            f"Supported Formats: {', '.join(self.FORMATS)}\n"
            f"Compression: {info['compression']}\n"
            f"Speed: {info['speed']}"
        )
