"""
ChainForgeLedger Database Module

Database abstraction layer for blockchain data storage.
"""

import json
import sqlite3
import threading
from typing import Dict, List, Optional
from chainforgeledger.utils.logger import get_logger


class Database:
    """
    Database abstraction layer for blockchain operations.
    
    Provides a unified interface for different database implementations.
    """
    
    def __init__(self, db_path: str = "chainforgeledger.db"):
        """
        Initialize database.
        
        Args:
            db_path: Database file path
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.lock = threading.Lock()
        self.logger = get_logger(__name__)
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self.logger.debug(f"Connected to database: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables."""
        try:
            # Blocks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_index INTEGER UNIQUE NOT NULL,
                    previous_hash TEXT NOT NULL,
                    block_hash TEXT UNIQUE NOT NULL,
                    merkle_root TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    difficulty REAL NOT NULL,
                    nonce INTEGER NOT NULL,
                    transactions TEXT NOT NULL,
                    miner_address TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    data TEXT,
                    signature TEXT NOT NULL,
                    block_index INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (block_index) REFERENCES blocks(block_index)
                )
            ''')
            
            # State table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    address TEXT PRIMARY KEY,
                    balance REAL NOT NULL DEFAULT 0,
                    nonce INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Contracts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS contracts (
                    contract_address TEXT PRIMARY KEY,
                    source_code TEXT NOT NULL,
                    bytecode TEXT NOT NULL,
                    language TEXT NOT NULL,
                    compiler_options TEXT,
                    deployed_at REAL NOT NULL,
                    state TEXT NOT NULL DEFAULT 'deployed',
                    bytecode_hash TEXT NOT NULL,
                    source_code_hash TEXT NOT NULL,
                    updated_at REAL,
                    deactivated_at REAL,
                    activated_at REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Contract storage table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_storage (
                    contract_address TEXT,
                    storage_key TEXT,
                    storage_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (contract_address, storage_key),
                    FOREIGN KEY (contract_address) REFERENCES contracts(contract_address)
                )
            ''')
            
            # Wallets table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    address TEXT PRIMARY KEY,
                    public_key TEXT NOT NULL,
                    private_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Nodes table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    last_seen REAL,
                    is_connected INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Mempool table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS mempool (
                    transaction_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    data TEXT,
                    signature TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Stats table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
             # Staking table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS staking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validator_address TEXT NOT NULL,
                    staker_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    type TEXT NOT NULL,
                    block_height INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (block_height) REFERENCES blocks(block_index)
                )
            ''')
            
            # Rewards table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validator_address TEXT NOT NULL,
                    recipient_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    block_height INTEGER,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (block_height) REFERENCES blocks(block_index)
                )
            ''')
            
            # Unstaking queue table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS unstaking_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validator_address TEXT NOT NULL,
                    staker_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    request_time REAL NOT NULL,
                    release_time REAL NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # DAO table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daos (
                    dao_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    creator_address TEXT NOT NULL,
                    total_token_supply REAL NOT NULL,
                    quorum_threshold REAL NOT NULL,
                    approval_threshold REAL NOT NULL,
                    voting_period REAL NOT NULL,
                    proposal_fee REAL NOT NULL,
                    governance_token TEXT NOT NULL,
                    treasury TEXT,
                    members TEXT,
                    config TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')
            
            # Proposals table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    dao_id TEXT NOT NULL,
                    proposer_address TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    quorum_required REAL NOT NULL,
                    approval_threshold REAL NOT NULL,
                    voting_duration REAL NOT NULL,
                    start_time REAL,
                    end_time REAL,
                    yes_votes REAL NOT NULL DEFAULT 0,
                    no_votes REAL NOT NULL DEFAULT 0,
                    abstain_votes REAL NOT NULL DEFAULT 0,
                    total_votes REAL NOT NULL DEFAULT 0,
                    executed INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (dao_id) REFERENCES daos(dao_id)
                )
            ''')
            
            # Votes table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT NOT NULL,
                    voter_address TEXT NOT NULL,
                    vote TEXT NOT NULL,
                    voting_power REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            ''')
            
            # Lending pools table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS lending_pools (
                    pool_id TEXT PRIMARY KEY,
                    token TEXT NOT NULL,
                    total_deposits REAL NOT NULL DEFAULT 0,
                    total_borrowed REAL NOT NULL DEFAULT 0,
                    interest_rate REAL NOT NULL,
                    collateral_ratio REAL NOT NULL,
                    liquidation_threshold REAL NOT NULL,
                    liquidation_bonus REAL NOT NULL,
                    last_interest_update REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Lenders table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS lenders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id TEXT NOT NULL,
                    lender_address TEXT NOT NULL,
                    principal REAL NOT NULL DEFAULT 0,
                    interest_earned REAL NOT NULL DEFAULT 0,
                    last_deposit_time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES lending_pools(pool_id),
                    UNIQUE(pool_id, lender_address)
                )
            ''')
            
            # Borrowers table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS borrowers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id TEXT NOT NULL,
                    borrower_address TEXT NOT NULL,
                    principal REAL NOT NULL DEFAULT 0,
                    interest_owed REAL NOT NULL DEFAULT 0,
                    collateral_token TEXT NOT NULL,
                    collateral_amount REAL NOT NULL DEFAULT 0,
                    last_borrow_time REAL NOT NULL,
                    liquidation_price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES lending_pools(pool_id),
                    UNIQUE(pool_id, borrower_address)
                )
            ''')
            
            # Lending pool history table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS lending_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    collateral_amount REAL,
                    collateral_token TEXT,
                    liquidator_address TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES lending_pools(pool_id)
                )
            ''')
            
            # Treasury table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS treasury (
                    treasury_address TEXT PRIMARY KEY,
                    dao_id TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0,
                    proposal_fee REAL NOT NULL,
                    minimum_proposal_amount REAL NOT NULL,
                    transaction_counter INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dao_id) REFERENCES daos(dao_id)
                )
            ''')
            
            # Treasury transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS treasury_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    treasury_address TEXT NOT NULL,
                    type TEXT NOT NULL,
                    from_address TEXT,
                    to_address TEXT,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL DEFAULT 0,
                    proposal_id TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (treasury_address) REFERENCES treasury(treasury_address)
                )
            ''')
            
            # Funding proposals table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS funding_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    treasury_address TEXT NOT NULL,
                    proposer_address TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    recipient_address TEXT NOT NULL,
                    status TEXT NOT NULL,
                    submission_time REAL NOT NULL,
                    votes TEXT,
                    vote_count INTEGER NOT NULL DEFAULT 0,
                    vote_threshold REAL NOT NULL,
                    voting_period REAL NOT NULL,
                    finalized INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (treasury_address) REFERENCES treasury(treasury_address)
                )
            ''')
            
            # Indexes for performance optimization
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_staking_validator ON staking(validator_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_staking_staker ON staking(staker_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_rewards_recipient ON rewards(recipient_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_rewards_validator ON rewards(validator_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_proposals_dao ON proposals(dao_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_proposal ON votes(proposal_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_voter ON votes(voter_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_lenders_pool ON lenders(pool_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_borrowers_pool ON borrowers(pool_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_lending_history_pool ON lending_history(pool_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_treasury_transactions_treasury ON treasury_transactions(treasury_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_proposals_treasury ON funding_proposals(treasury_address)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_proposals_status ON funding_proposals(status)')
            
            self.connection.commit()
            self.logger.debug("Database tables created/verified")
        
        except Exception as e:
            self.logger.error(f"Table creation failed: {e}")
            self.connection.rollback()
            raise
    
    # Block operations
    def save_block(self, block_data: Dict) -> int:
        """
        Save block to database.
        
        Args:
            block_data: Block data dictionary
            
        Returns:
            Number of affected rows
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO blocks (
                        block_index, previous_hash, block_hash, merkle_root,
                        timestamp, difficulty, nonce, transactions,
                        miner_address, hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    block_data['block_index'],
                    block_data['previous_hash'],
                    block_data['block_hash'],
                    block_data['merkle_root'],
                    block_data['timestamp'],
                    block_data['difficulty'],
                    block_data['nonce'],
                    json.dumps(block_data['transactions']),
                    block_data['miner_address'],
                    block_data['block_hash']
                ))
                
                self.connection.commit()
                return self.cursor.rowcount
                
        except Exception as e:
            self.logger.error(f"Failed to save block: {e}")
            self.connection.rollback()
            raise
    
    def get_block(self, block_index: int) -> Optional[Dict]:
        """
        Get block by index.
        
        Args:
            block_index: Block index
            
        Returns:
            Block data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM blocks WHERE block_index = ?
                ''', (block_index,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_block(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get block: {e}")
            return None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        """
        Get block by hash.
        
        Args:
            block_hash: Block hash
            
        Returns:
            Block data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM blocks WHERE block_hash = ?
                ''', (block_hash,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_block(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get block by hash: {e}")
            return None
    
    def get_last_block(self) -> Optional[Dict]:
        """
        Get last block.
        
        Returns:
            Last block data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM blocks ORDER BY block_index DESC LIMIT 1
                ''')
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_block(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get last block: {e}")
            return None
    
    def get_all_blocks(self) -> List[Dict]:
        """
        Get all blocks.
        
        Returns:
            List of blocks
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM blocks ORDER BY block_index ASC
                ''')
                
                blocks = []
                for row in self.cursor.fetchall():
                    blocks.append(self._row_to_block(row))
                
                return blocks
                
        except Exception as e:
            self.logger.error(f"Failed to get all blocks: {e}")
            return []
    
    def get_blocks_range(self, start_index: int, end_index: int) -> List[Dict]:
        """
        Get blocks in range.
        
        Args:
            start_index: Start block index
            end_index: End block index
            
        Returns:
            List of blocks
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM blocks
                    WHERE block_index BETWEEN ? AND ?
                    ORDER BY block_index ASC
                ''', (start_index, end_index))
                
                blocks = []
                for row in self.cursor.fetchall():
                    blocks.append(self._row_to_block(row))
                
                return blocks
                
        except Exception as e:
            self.logger.error(f"Failed to get blocks range: {e}")
            return []
    
    def get_block_count(self) -> int:
        """
        Get number of blocks.
        
        Returns:
            Block count
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT COUNT(*) FROM blocks
                ''')
                
                return self.cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Failed to get block count: {e}")
            return 0
    
    # Transaction operations
    def save_transaction(self, transaction_data: Dict, block_index: int = None):
        """
        Save transaction to database.
        
        Args:
            transaction_data: Transaction data
            block_index: Block index
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO transactions (
                        transaction_id, sender, recipient, amount, fee,
                        timestamp, data, signature, block_index
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction_data['transaction_id'],
                    transaction_data['sender'],
                    transaction_data['recipient'],
                    transaction_data['amount'],
                    transaction_data['fee'],
                    transaction_data['timestamp'],
                    json.dumps(transaction_data.get('data', {})),
                    transaction_data['signature'],
                    block_index
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save transaction: {e}")
            self.connection.rollback()
            raise
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM transactions WHERE transaction_id = ?
                ''', (transaction_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_transaction(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get transaction: {e}")
            return None
    
    def get_transactions_by_block(self, block_index: int) -> List[Dict]:
        """
        Get transactions by block index.
        
        Args:
            block_index: Block index
            
        Returns:
            List of transactions
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM transactions WHERE block_index = ?
                ''', (block_index,))
                
                transactions = []
                for row in self.cursor.fetchall():
                    transactions.append(self._row_to_transaction(row))
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Failed to get transactions by block: {e}")
            return []
    
    def get_transactions_by_address(self, address: str) -> List[Dict]:
        """
        Get transactions by address.
        
        Args:
            address: Address
            
        Returns:
            List of transactions
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM transactions WHERE sender = ? OR recipient = ?
                ''', (address, address))
                
                transactions = []
                for row in self.cursor.fetchall():
                    transactions.append(self._row_to_transaction(row))
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Failed to get transactions by address: {e}")
            return []
    
    def get_all_transactions(self) -> List[Dict]:
        """
        Get all transactions.
        
        Returns:
            List of transactions
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM transactions ORDER BY timestamp DESC
                ''')
                
                transactions = []
                for row in self.cursor.fetchall():
                    transactions.append(self._row_to_transaction(row))
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Failed to get all transactions: {e}")
            return []
    
    # State operations
    def save_state(self, address: str, balance: float, nonce: int = 0):
        """
        Save state.
        
        Args:
            address: Address
            balance: Balance
            nonce: Nonce
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO state (address, balance, nonce, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (address, balance, nonce))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            self.connection.rollback()
            raise
    
    def get_state(self, address: str) -> Optional[Dict]:
        """
        Get state.
        
        Args:
            address: Address
            
        Returns:
            State data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM state WHERE address = ?
                ''', (address,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_state(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get state: {e}")
            return None
    
    def get_all_states(self) -> List[Dict]:
        """
        Get all states.
        
        Returns:
            List of states
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM state
                ''')
                
                states = []
                for row in self.cursor.fetchall():
                    states.append(self._row_to_state(row))
                
                return states
                
        except Exception as e:
            self.logger.error(f"Failed to get all states: {e}")
            return []
    
    # Contract operations
    def save_contract(self, contract_data: Dict):
        """
        Save contract.
        
        Args:
            contract_data: Contract data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO contracts (
                        contract_address, source_code, bytecode, language,
                        compiler_options, deployed_at, state, bytecode_hash,
                        source_code_hash, updated_at, deactivated_at, activated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    contract_data['contract_address'],
                    contract_data['source_code'],
                    contract_data['bytecode'],
                    contract_data['language'],
                    json.dumps(contract_data.get('compiler_options', {})),
                    contract_data['deployed_at'],
                    contract_data.get('state', 'deployed'),
                    contract_data['bytecode_hash'],
                    contract_data['source_code_hash'],
                    contract_data.get('updated_at'),
                    contract_data.get('deactivated_at'),
                    contract_data.get('activated_at')
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save contract: {e}")
            self.connection.rollback()
            raise
    
    def get_contract(self, contract_address: str) -> Optional[Dict]:
        """
        Get contract.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM contracts WHERE contract_address = ?
                ''', (contract_address,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_contract(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get contract: {e}")
            return None
    
    def get_all_contracts(self) -> List[Dict]:
        """
        Get all contracts.
        
        Returns:
            List of contracts
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM contracts
                ''')
                
                contracts = []
                for row in self.cursor.fetchall():
                    contracts.append(self._row_to_contract(row))
                
                return contracts
                
        except Exception as e:
            self.logger.error(f"Failed to get all contracts: {e}")
            return []
    
    # Contract storage operations
    def save_contract_storage(self, contract_address: str, storage_key: str, storage_value: str):
        """
        Save contract storage.
        
        Args:
            contract_address: Contract address
            storage_key: Storage key
            storage_value: Storage value
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO contract_storage (
                        contract_address, storage_key, storage_value, updated_at
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (contract_address, storage_key, storage_value))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save contract storage: {e}")
            self.connection.rollback()
            raise
    
    def get_contract_storage(self, contract_address: str) -> Dict:
        """
        Get contract storage.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract storage
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT storage_key, storage_value FROM contract_storage
                    WHERE contract_address = ?
                ''', (contract_address,))
                
                storage = {}
                for row in self.cursor.fetchall():
                    storage[row['storage_key']] = row['storage_value']
                
                return storage
                
        except Exception as e:
            self.logger.error(f"Failed to get contract storage: {e}")
            return {}
    
    # Wallet operations
    def save_wallet(self, wallet_data: Dict):
        """
        Save wallet.
        
        Args:
            wallet_data: Wallet data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO wallets (
                        address, public_key, private_key, updated_at
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    wallet_data['address'],
                    wallet_data['public_key'],
                    wallet_data['private_key']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save wallet: {e}")
            self.connection.rollback()
            raise
    
    def get_wallet(self, address: str) -> Optional[Dict]:
        """
        Get wallet.
        
        Args:
            address: Address
            
        Returns:
            Wallet data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM wallets WHERE address = ?
                ''', (address,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_wallet(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get wallet: {e}")
            return None
    
    def get_all_wallets(self) -> List[Dict]:
        """
        Get all wallets.
        
        Returns:
            List of wallets
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM wallets
                ''')
                
                wallets = []
                for row in self.cursor.fetchall():
                    wallets.append(self._row_to_wallet(row))
                
                return wallets
                
        except Exception as e:
            self.logger.error(f"Failed to get all wallets: {e}")
            return []
    
    # Node operations
    def save_node(self, node_data: Dict):
        """
        Save node.
        
        Args:
            node_data: Node data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO nodes (
                        node_id, address, port, last_seen, is_connected, updated_at
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    node_data['node_id'],
                    node_data['address'],
                    node_data['port'],
                    node_data['last_seen'],
                    node_data['is_connected']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save node: {e}")
            self.connection.rollback()
            raise
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get node.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM nodes WHERE node_id = ?
                ''', (node_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return self._row_to_node(row)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get node: {e}")
            return None
    
    def get_all_nodes(self) -> List[Dict]:
        """
        Get all nodes.
        
        Returns:
            List of nodes
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM nodes
                ''')
                
                nodes = []
                for row in self.cursor.fetchall():
                    nodes.append(self._row_to_node(row))
                
                return nodes
                
        except Exception as e:
            self.logger.error(f"Failed to get all nodes: {e}")
            return []
    
    # Mempool operations
    def save_to_mempool(self, transaction_data: Dict):
        """
        Save transaction to mempool.
        
        Args:
            transaction_data: Transaction data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO mempool (
                        transaction_id, sender, recipient, amount, fee,
                        timestamp, data, signature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction_data['transaction_id'],
                    transaction_data['sender'],
                    transaction_data['recipient'],
                    transaction_data['amount'],
                    transaction_data['fee'],
                    transaction_data['timestamp'],
                    json.dumps(transaction_data.get('data', {})),
                    transaction_data['signature']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save to mempool: {e}")
            self.connection.rollback()
            raise
    
    def get_mempool_transactions(self) -> List[Dict]:
        """
        Get mempool transactions.
        
        Returns:
            List of mempool transactions
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM mempool ORDER BY fee DESC
                ''')
                
                transactions = []
                for row in self.cursor.fetchall():
                    transactions.append(self._row_to_mempool_transaction(row))
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Failed to get mempool transactions: {e}")
            return []
    
    def remove_from_mempool(self, transaction_id: str):
        """
        Remove transaction from mempool.
        
        Args:
            transaction_id: Transaction ID
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    DELETE FROM mempool WHERE transaction_id = ?
                ''', (transaction_id,))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to remove from mempool: {e}")
            self.connection.rollback()
            raise
    
    # Staking operations
    def save_staking(self, staking_data: Dict):
        """
        Save staking data.
        
        Args:
            staking_data: Staking data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO staking (
                        validator_address, staker_address, amount, timestamp, type, block_height
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    staking_data['validator_address'],
                    staking_data['staker_address'],
                    staking_data['amount'],
                    staking_data['timestamp'],
                    staking_data['type'],
                    staking_data.get('block_height')
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save staking data: {e}")
            self.connection.rollback()
            raise
    
    def get_staking_by_validator(self, validator_address: str) -> List[Dict]:
        """
        Get staking data by validator address.
        
        Args:
            validator_address: Validator address
            
        Returns:
            List of staking data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM staking WHERE validator_address = ? ORDER BY timestamp DESC
                ''', (validator_address,))
                
                staking = []
                for row in self.cursor.fetchall():
                    staking.append({
                        'validator_address': row['validator_address'],
                        'staker_address': row['staker_address'],
                        'amount': row['amount'],
                        'timestamp': row['timestamp'],
                        'type': row['type'],
                        'block_height': row['block_height']
                    })
                
                return staking
                
        except Exception as e:
            self.logger.error(f"Failed to get staking data by validator: {e}")
            return []
    
    def get_staking_by_staker(self, staker_address: str) -> List[Dict]:
        """
        Get staking data by staker address.
        
        Args:
            staker_address: Staker address
            
        Returns:
            List of staking data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM staking WHERE staker_address = ? ORDER BY timestamp DESC
                ''', (staker_address,))
                
                staking = []
                for row in self.cursor.fetchall():
                    staking.append({
                        'validator_address': row['validator_address'],
                        'staker_address': row['staker_address'],
                        'amount': row['amount'],
                        'timestamp': row['timestamp'],
                        'type': row['type'],
                        'block_height': row['block_height']
                    })
                
                return staking
                
        except Exception as e:
            self.logger.error(f"Failed to get staking data by staker: {e}")
            return []
    
    # Rewards operations
    def save_reward(self, reward_data: Dict):
        """
        Save reward data.
        
        Args:
            reward_data: Reward data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO rewards (
                        validator_address, recipient_address, amount, type, block_height, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    reward_data['validator_address'],
                    reward_data['recipient_address'],
                    reward_data['amount'],
                    reward_data['type'],
                    reward_data.get('block_height'),
                    reward_data['timestamp']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save reward data: {e}")
            self.connection.rollback()
            raise
    
    def get_rewards_by_recipient(self, recipient_address: str) -> List[Dict]:
        """
        Get rewards by recipient address.
        
        Args:
            recipient_address: Recipient address
            
        Returns:
            List of rewards
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM rewards WHERE recipient_address = ? ORDER BY timestamp DESC
                ''', (recipient_address,))
                
                rewards = []
                for row in self.cursor.fetchall():
                    rewards.append({
                        'validator_address': row['validator_address'],
                        'recipient_address': row['recipient_address'],
                        'amount': row['amount'],
                        'type': row['type'],
                        'block_height': row['block_height'],
                        'timestamp': row['timestamp']
                    })
                
                return rewards
                
        except Exception as e:
            self.logger.error(f"Failed to get rewards by recipient: {e}")
            return []
    
    def get_rewards_by_validator(self, validator_address: str) -> List[Dict]:
        """
        Get rewards by validator address.
        
        Args:
            validator_address: Validator address
            
        Returns:
            List of rewards
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM rewards WHERE validator_address = ? ORDER BY timestamp DESC
                ''', (validator_address,))
                
                rewards = []
                for row in self.cursor.fetchall():
                    rewards.append({
                        'validator_address': row['validator_address'],
                        'recipient_address': row['recipient_address'],
                        'amount': row['amount'],
                        'type': row['type'],
                        'block_height': row['block_height'],
                        'timestamp': row['timestamp']
                    })
                
                return rewards
                
        except Exception as e:
            self.logger.error(f"Failed to get rewards by validator: {e}")
            return []
    
    # Unstaking queue operations
    def save_unstaking_queue(self, unstaking_data: Dict):
        """
        Save unstaking queue data.
        
        Args:
            unstaking_data: Unstaking queue data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO unstaking_queue (
                        validator_address, staker_address, amount, request_time, release_time, completed
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    unstaking_data['validator_address'],
                    unstaking_data['staker_address'],
                    unstaking_data['amount'],
                    unstaking_data['request_time'],
                    unstaking_data['release_time'],
                    1 if unstaking_data.get('completed', False) else 0
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save unstaking queue data: {e}")
            self.connection.rollback()
            raise
    
    def get_unstaking_queue(self, completed: bool = False) -> List[Dict]:
        """
        Get unstaking queue data.
        
        Args:
            completed: Whether to get completed unstaking requests
            
        Returns:
            List of unstaking queue data
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM unstaking_queue WHERE completed = ? ORDER BY request_time DESC
                ''', (1 if completed else 0,))
                
                unstaking_queue = []
                for row in self.cursor.fetchall():
                    unstaking_queue.append({
                        'validator_address': row['validator_address'],
                        'staker_address': row['staker_address'],
                        'amount': row['amount'],
                        'request_time': row['request_time'],
                        'release_time': row['release_time'],
                        'completed': bool(row['completed'])
                    })
                
                return unstaking_queue
                
        except Exception as e:
            self.logger.error(f"Failed to get unstaking queue: {e}")
            return []
    
    # DAO operations
    def save_dao(self, dao_data: Dict):
        """
        Save DAO data.
        
        Args:
            dao_data: DAO data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO daos (
                        dao_id, name, description, creator_address, total_token_supply,
                        quorum_threshold, approval_threshold, voting_period, proposal_fee,
                        governance_token, treasury, members, config, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dao_data['dao_id'],
                    dao_data['name'],
                    dao_data.get('description'),
                    dao_data['creator_address'],
                    dao_data['total_token_supply'],
                    dao_data['quorum_threshold'],
                    dao_data['approval_threshold'],
                    dao_data['voting_period'],
                    dao_data['proposal_fee'],
                    dao_data['governance_token'],
                    json.dumps(dao_data.get('treasury', {})),
                    json.dumps(dao_data.get('members', {})),
                    json.dumps(dao_data.get('config', {})),
                    dao_data['created_at'],
                    dao_data['updated_at']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save DAO data: {e}")
            self.connection.rollback()
            raise
    
    def get_dao(self, dao_id: str) -> Optional[Dict]:
        """
        Get DAO data by ID.
        
        Args:
            dao_id: DAO ID
            
        Returns:
            DAO data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM daos WHERE dao_id = ?
                ''', (dao_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'dao_id': row['dao_id'],
                        'name': row['name'],
                        'description': row['description'],
                        'creator_address': row['creator_address'],
                        'total_token_supply': row['total_token_supply'],
                        'quorum_threshold': row['quorum_threshold'],
                        'approval_threshold': row['approval_threshold'],
                        'voting_period': row['voting_period'],
                        'proposal_fee': row['proposal_fee'],
                        'governance_token': row['governance_token'],
                        'treasury': json.loads(row['treasury']),
                        'members': json.loads(row['members']),
                        'config': json.loads(row['config']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get DAO: {e}")
            return None
    
    def get_all_daos(self) -> List[Dict]:
        """
        Get all DAOs.
        
        Returns:
            List of DAOs
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM daos
                ''')
                
                daos = []
                for row in self.cursor.fetchall():
                    daos.append({
                        'dao_id': row['dao_id'],
                        'name': row['name'],
                        'description': row['description'],
                        'creator_address': row['creator_address'],
                        'total_token_supply': row['total_token_supply'],
                        'quorum_threshold': row['quorum_threshold'],
                        'approval_threshold': row['approval_threshold'],
                        'voting_period': row['voting_period'],
                        'proposal_fee': row['proposal_fee'],
                        'governance_token': row['governance_token'],
                        'treasury': json.loads(row['treasury']),
                        'members': json.loads(row['members']),
                        'config': json.loads(row['config']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return daos
                
        except Exception as e:
            self.logger.error(f"Failed to get all DAOs: {e}")
            return []
    
    # Proposals operations
    def save_proposal(self, proposal_data: Dict):
        """
        Save proposal data.
        
        Args:
            proposal_data: Proposal data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO proposals (
                        proposal_id, dao_id, proposer_address, title, description, type,
                        status, quorum_required, approval_threshold, voting_duration,
                        start_time, end_time, yes_votes, no_votes, abstain_votes,
                        total_votes, executed, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    proposal_data['proposal_id'],
                    proposal_data['dao_id'],
                    proposal_data['proposer_address'],
                    proposal_data['title'],
                    proposal_data.get('description'),
                    proposal_data['type'],
                    proposal_data['status'],
                    proposal_data['quorum_required'],
                    proposal_data['approval_threshold'],
                    proposal_data['voting_duration'],
                    proposal_data.get('start_time'),
                    proposal_data.get('end_time'),
                    proposal_data.get('yes_votes', 0),
                    proposal_data.get('no_votes', 0),
                    proposal_data.get('abstain_votes', 0),
                    proposal_data.get('total_votes', 0),
                    1 if proposal_data.get('executed', False) else 0,
                    proposal_data['created_at'],
                    proposal_data['updated_at']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save proposal data: {e}")
            self.connection.rollback()
            raise
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """
        Get proposal by ID.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM proposals WHERE proposal_id = ?
                ''', (proposal_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'proposal_id': row['proposal_id'],
                        'dao_id': row['dao_id'],
                        'proposer_address': row['proposer_address'],
                        'title': row['title'],
                        'description': row['description'],
                        'type': row['type'],
                        'status': row['status'],
                        'quorum_required': row['quorum_required'],
                        'approval_threshold': row['approval_threshold'],
                        'voting_duration': row['voting_duration'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'yes_votes': row['yes_votes'],
                        'no_votes': row['no_votes'],
                        'abstain_votes': row['abstain_votes'],
                        'total_votes': row['total_votes'],
                        'executed': bool(row['executed']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get proposal: {e}")
            return None
    
    def get_proposals_by_dao(self, dao_id: str) -> List[Dict]:
        """
        Get proposals by DAO ID.
        
        Args:
            dao_id: DAO ID
            
        Returns:
            List of proposals
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM proposals WHERE dao_id = ? ORDER BY created_at DESC
                ''', (dao_id,))
                
                proposals = []
                for row in self.cursor.fetchall():
                    proposals.append({
                        'proposal_id': row['proposal_id'],
                        'dao_id': row['dao_id'],
                        'proposer_address': row['proposer_address'],
                        'title': row['title'],
                        'description': row['description'],
                        'type': row['type'],
                        'status': row['status'],
                        'quorum_required': row['quorum_required'],
                        'approval_threshold': row['approval_threshold'],
                        'voting_duration': row['voting_duration'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'yes_votes': row['yes_votes'],
                        'no_votes': row['no_votes'],
                        'abstain_votes': row['abstain_votes'],
                        'total_votes': row['total_votes'],
                        'executed': bool(row['executed']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return proposals
                
        except Exception as e:
            self.logger.error(f"Failed to get proposals by DAO: {e}")
            return []
    
    def get_proposals_by_status(self, status: str) -> List[Dict]:
        """
        Get proposals by status.
        
        Args:
            status: Proposal status
            
        Returns:
            List of proposals
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC
                ''', (status,))
                
                proposals = []
                for row in self.cursor.fetchall():
                    proposals.append({
                        'proposal_id': row['proposal_id'],
                        'dao_id': row['dao_id'],
                        'proposer_address': row['proposer_address'],
                        'title': row['title'],
                        'description': row['description'],
                        'type': row['type'],
                        'status': row['status'],
                        'quorum_required': row['quorum_required'],
                        'approval_threshold': row['approval_threshold'],
                        'voting_duration': row['voting_duration'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'yes_votes': row['yes_votes'],
                        'no_votes': row['no_votes'],
                        'abstain_votes': row['abstain_votes'],
                        'total_votes': row['total_votes'],
                        'executed': bool(row['executed']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return proposals
                
        except Exception as e:
            self.logger.error(f"Failed to get proposals by status: {e}")
            return []
    
    # Votes operations
    def save_vote(self, vote_data: Dict):
        """
        Save vote data.
        
        Args:
            vote_data: Vote data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO votes (
                        proposal_id, voter_address, vote, voting_power, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    vote_data['proposal_id'],
                    vote_data['voter_address'],
                    vote_data['vote'],
                    vote_data['voting_power'],
                    vote_data['timestamp']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save vote data: {e}")
            self.connection.rollback()
            raise
    
    def get_votes_by_proposal(self, proposal_id: str) -> List[Dict]:
        """
        Get votes by proposal ID.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            List of votes
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM votes WHERE proposal_id = ? ORDER BY timestamp DESC
                ''', (proposal_id,))
                
                votes = []
                for row in self.cursor.fetchall():
                    votes.append({
                        'proposal_id': row['proposal_id'],
                        'voter_address': row['voter_address'],
                        'vote': row['vote'],
                        'voting_power': row['voting_power'],
                        'timestamp': row['timestamp']
                    })
                
                return votes
                
        except Exception as e:
            self.logger.error(f"Failed to get votes by proposal: {e}")
            return []
    
    def get_votes_by_voter(self, voter_address: str) -> List[Dict]:
        """
        Get votes by voter address.
        
        Args:
            voter_address: Voter address
            
        Returns:
            List of votes
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM votes WHERE voter_address = ? ORDER BY timestamp DESC
                ''', (voter_address,))
                
                votes = []
                for row in self.cursor.fetchall():
                    votes.append({
                        'proposal_id': row['proposal_id'],
                        'voter_address': row['voter_address'],
                        'vote': row['vote'],
                        'voting_power': row['voting_power'],
                        'timestamp': row['timestamp']
                    })
                
                return votes
                
        except Exception as e:
            self.logger.error(f"Failed to get votes by voter: {e}")
            return []
    
    # Lending operations
    def save_lending_pool(self, pool_data: Dict):
        """
        Save lending pool data.
        
        Args:
            pool_data: Lending pool data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO lending_pools (
                        pool_id, token, total_deposits, total_borrowed, interest_rate,
                        collateral_ratio, liquidation_threshold, liquidation_bonus,
                        last_interest_update, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    pool_data['pool_id'],
                    pool_data['token'],
                    pool_data.get('total_deposits', 0),
                    pool_data.get('total_borrowed', 0),
                    pool_data['interest_rate'],
                    pool_data['collateral_ratio'],
                    pool_data['liquidation_threshold'],
                    pool_data['liquidation_bonus'],
                    pool_data['last_interest_update']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save lending pool data: {e}")
            self.connection.rollback()
            raise
    
    def get_lending_pool(self, pool_id: str) -> Optional[Dict]:
        """
        Get lending pool by ID.
        
        Args:
            pool_id: Lending pool ID
            
        Returns:
            Lending pool data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM lending_pools WHERE pool_id = ?
                ''', (pool_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'pool_id': row['pool_id'],
                        'token': row['token'],
                        'total_deposits': row['total_deposits'],
                        'total_borrowed': row['total_borrowed'],
                        'interest_rate': row['interest_rate'],
                        'collateral_ratio': row['collateral_ratio'],
                        'liquidation_threshold': row['liquidation_threshold'],
                        'liquidation_bonus': row['liquidation_bonus'],
                        'last_interest_update': row['last_interest_update'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get lending pool: {e}")
            return None
    
    def get_all_lending_pools(self) -> List[Dict]:
        """
        Get all lending pools.
        
        Returns:
            List of lending pools
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM lending_pools
                ''')
                
                pools = []
                for row in self.cursor.fetchall():
                    pools.append({
                        'pool_id': row['pool_id'],
                        'token': row['token'],
                        'total_deposits': row['total_deposits'],
                        'total_borrowed': row['total_borrowed'],
                        'interest_rate': row['interest_rate'],
                        'collateral_ratio': row['collateral_ratio'],
                        'liquidation_threshold': row['liquidation_threshold'],
                        'liquidation_bonus': row['liquidation_bonus'],
                        'last_interest_update': row['last_interest_update'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return pools
                
        except Exception as e:
            self.logger.error(f"Failed to get all lending pools: {e}")
            return []
    
    def save_lender(self, lender_data: Dict):
        """
        Save lender data.
        
        Args:
            lender_data: Lender data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO lenders (
                        pool_id, lender_address, principal, interest_earned, last_deposit_time, updated_at
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    lender_data['pool_id'],
                    lender_data['lender_address'],
                    lender_data.get('principal', 0),
                    lender_data.get('interest_earned', 0),
                    lender_data['last_deposit_time']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save lender data: {e}")
            self.connection.rollback()
            raise
    
    def get_lender(self, pool_id: str, lender_address: str) -> Optional[Dict]:
        """
        Get lender by pool and address.
        
        Args:
            pool_id: Lending pool ID
            lender_address: Lender address
            
        Returns:
            Lender data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM lenders WHERE pool_id = ? AND lender_address = ?
                ''', (pool_id, lender_address))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'pool_id': row['pool_id'],
                        'lender_address': row['lender_address'],
                        'principal': row['principal'],
                        'interest_earned': row['interest_earned'],
                        'last_deposit_time': row['last_deposit_time'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get lender: {e}")
            return None
    
    def get_lenders_by_pool(self, pool_id: str) -> List[Dict]:
        """
        Get lenders by pool ID.
        
        Args:
            pool_id: Lending pool ID
            
        Returns:
            List of lenders
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM lenders WHERE pool_id = ?
                ''', (pool_id,))
                
                lenders = []
                for row in self.cursor.fetchall():
                    lenders.append({
                        'pool_id': row['pool_id'],
                        'lender_address': row['lender_address'],
                        'principal': row['principal'],
                        'interest_earned': row['interest_earned'],
                        'last_deposit_time': row['last_deposit_time'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return lenders
                
        except Exception as e:
            self.logger.error(f"Failed to get lenders by pool: {e}")
            return []
    
    def save_borrower(self, borrower_data: Dict):
        """
        Save borrower data.
        
        Args:
            borrower_data: Borrower data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO borrowers (
                        pool_id, borrower_address, principal, interest_owed,
                        collateral_token, collateral_amount, last_borrow_time,
                        liquidation_price, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    borrower_data['pool_id'],
                    borrower_data['borrower_address'],
                    borrower_data.get('principal', 0),
                    borrower_data.get('interest_owed', 0),
                    borrower_data['collateral_token'],
                    borrower_data.get('collateral_amount', 0),
                    borrower_data['last_borrow_time'],
                    borrower_data.get('liquidation_price')
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save borrower data: {e}")
            self.connection.rollback()
            raise
    
    def get_borrower(self, pool_id: str, borrower_address: str) -> Optional[Dict]:
        """
        Get borrower by pool and address.
        
        Args:
            pool_id: Lending pool ID
            borrower_address: Borrower address
            
        Returns:
            Borrower data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM borrowers WHERE pool_id = ? AND borrower_address = ?
                ''', (pool_id, borrower_address))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'pool_id': row['pool_id'],
                        'borrower_address': row['borrower_address'],
                        'principal': row['principal'],
                        'interest_owed': row['interest_owed'],
                        'collateral_token': row['collateral_token'],
                        'collateral_amount': row['collateral_amount'],
                        'last_borrow_time': row['last_borrow_time'],
                        'liquidation_price': row['liquidation_price'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get borrower: {e}")
            return None
    
    def get_borrowers_by_pool(self, pool_id: str) -> List[Dict]:
        """
        Get borrowers by pool ID.
        
        Args:
            pool_id: Lending pool ID
            
        Returns:
            List of borrowers
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM borrowers WHERE pool_id = ?
                ''', (pool_id,))
                
                borrowers = []
                for row in self.cursor.fetchall():
                    borrowers.append({
                        'pool_id': row['pool_id'],
                        'borrower_address': row['borrower_address'],
                        'principal': row['principal'],
                        'interest_owed': row['interest_owed'],
                        'collateral_token': row['collateral_token'],
                        'collateral_amount': row['collateral_amount'],
                        'last_borrow_time': row['last_borrow_time'],
                        'liquidation_price': row['liquidation_price'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return borrowers
                
        except Exception as e:
            self.logger.error(f"Failed to get borrowers by pool: {e}")
            return []
    
    def save_lending_history(self, history_data: Dict):
        """
        Save lending history data.
        
        Args:
            history_data: Lending history data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO lending_history (
                        pool_id, type, address, amount, collateral_amount,
                        collateral_token, liquidator_address, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    history_data['pool_id'],
                    history_data['type'],
                    history_data['address'],
                    history_data['amount'],
                    history_data.get('collateral_amount'),
                    history_data.get('collateral_token'),
                    history_data.get('liquidator_address'),
                    history_data['timestamp']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save lending history: {e}")
            self.connection.rollback()
            raise
    
    def get_lending_history_by_pool(self, pool_id: str) -> List[Dict]:
        """
        Get lending history by pool ID.
        
        Args:
            pool_id: Lending pool ID
            
        Returns:
            List of lending history
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM lending_history WHERE pool_id = ? ORDER BY timestamp DESC
                ''', (pool_id,))
                
                history = []
                for row in self.cursor.fetchall():
                    history.append({
                        'pool_id': row['pool_id'],
                        'type': row['type'],
                        'address': row['address'],
                        'amount': row['amount'],
                        'collateral_amount': row['collateral_amount'],
                        'collateral_token': row['collateral_token'],
                        'liquidator_address': row['liquidator_address'],
                        'timestamp': row['timestamp']
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get lending history by pool: {e}")
            return []
    
    # Treasury operations
    def save_treasury(self, treasury_data: Dict):
        """
        Save treasury data.
        
        Args:
            treasury_data: Treasury data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO treasury (
                        treasury_address, dao_id, balance, proposal_fee,
                        minimum_proposal_amount, transaction_counter, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    treasury_data['treasury_address'],
                    treasury_data['dao_id'],
                    treasury_data.get('balance', 0),
                    treasury_data['proposal_fee'],
                    treasury_data['minimum_proposal_amount'],
                    treasury_data.get('transaction_counter', 0)
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save treasury data: {e}")
            self.connection.rollback()
            raise
    
    def get_treasury(self, treasury_address: str) -> Optional[Dict]:
        """
        Get treasury by address.
        
        Args:
            treasury_address: Treasury address
            
        Returns:
            Treasury data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM treasury WHERE treasury_address = ?
                ''', (treasury_address,))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'treasury_address': row['treasury_address'],
                        'dao_id': row['dao_id'],
                        'balance': row['balance'],
                        'proposal_fee': row['proposal_fee'],
                        'minimum_proposal_amount': row['minimum_proposal_amount'],
                        'transaction_counter': row['transaction_counter'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get treasury: {e}")
            return None
    
    def save_treasury_transaction(self, transaction_data: Dict):
        """
        Save treasury transaction data.
        
        Args:
            transaction_data: Treasury transaction data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO treasury_transactions (
                        transaction_id, treasury_address, type, from_address,
                        to_address, amount, fee, proposal_id, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction_data['transaction_id'],
                    transaction_data['treasury_address'],
                    transaction_data['type'],
                    transaction_data.get('from_address'),
                    transaction_data.get('to_address'),
                    transaction_data['amount'],
                    transaction_data.get('fee', 0),
                    transaction_data.get('proposal_id'),
                    transaction_data['timestamp']
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save treasury transaction: {e}")
            self.connection.rollback()
            raise
    
    def get_treasury_transactions(self, treasury_address: str, transaction_type: str = None) -> List[Dict]:
        """
        Get treasury transactions.
        
        Args:
            treasury_address: Treasury address
            transaction_type: Optional transaction type filter
            
        Returns:
            List of treasury transactions
        """
        try:
            with self.lock:
                if transaction_type:
                    self.cursor.execute('''
                        SELECT * FROM treasury_transactions 
                        WHERE treasury_address = ? AND type = ? 
                        ORDER BY timestamp DESC
                    ''', (treasury_address, transaction_type))
                else:
                    self.cursor.execute('''
                        SELECT * FROM treasury_transactions 
                        WHERE treasury_address = ? 
                        ORDER BY timestamp DESC
                    ''', (treasury_address,))
                
                transactions = []
                for row in self.cursor.fetchall():
                    transactions.append({
                        'transaction_id': row['transaction_id'],
                        'treasury_address': row['treasury_address'],
                        'type': row['type'],
                        'from_address': row['from_address'],
                        'to_address': row['to_address'],
                        'amount': row['amount'],
                        'fee': row['fee'],
                        'proposal_id': row['proposal_id'],
                        'timestamp': row['timestamp']
                    })
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Failed to get treasury transactions: {e}")
            return []
    
    def save_funding_proposal(self, proposal_data: Dict):
        """
        Save funding proposal data.
        
        Args:
            proposal_data: Funding proposal data dictionary
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO funding_proposals (
                        proposal_id, treasury_address, proposer_address, title,
                        description, amount, fee, recipient_address, status,
                        submission_time, votes, vote_count, vote_threshold,
                        voting_period, finalized
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    proposal_data['proposal_id'],
                    proposal_data['treasury_address'],
                    proposal_data['proposer_address'],
                    proposal_data['title'],
                    proposal_data.get('description'),
                    proposal_data['amount'],
                    proposal_data['fee'],
                    proposal_data['recipient_address'],
                    proposal_data['status'],
                    proposal_data['submission_time'],
                    json.dumps(proposal_data.get('votes', {})),
                    proposal_data.get('vote_count', 0),
                    proposal_data.get('vote_threshold', 0.66),
                    proposal_data.get('voting_period', 86400),
                    1 if proposal_data.get('finalized', False) else 0
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save funding proposal: {e}")
            self.connection.rollback()
            raise
    
    def get_funding_proposal(self, proposal_id: str) -> Optional[Dict]:
        """
        Get funding proposal by ID.
        
        Args:
            proposal_id: Funding proposal ID
            
        Returns:
            Funding proposal data or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT * FROM funding_proposals WHERE proposal_id = ?
                ''', (proposal_id,))
                
                row = self.cursor.fetchone()
                if row:
                    return {
                        'proposal_id': row['proposal_id'],
                        'treasury_address': row['treasury_address'],
                        'proposer_address': row['proposer_address'],
                        'title': row['title'],
                        'description': row['description'],
                        'amount': row['amount'],
                        'fee': row['fee'],
                        'recipient_address': row['recipient_address'],
                        'status': row['status'],
                        'submission_time': row['submission_time'],
                        'votes': json.loads(row['votes']),
                        'vote_count': row['vote_count'],
                        'vote_threshold': row['vote_threshold'],
                        'voting_period': row['voting_period'],
                        'finalized': bool(row['finalized'])
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get funding proposal: {e}")
            return None
    
    def get_funding_proposals_by_treasury(self, treasury_address: str, status: str = None) -> List[Dict]:
        """
        Get funding proposals by treasury address.
        
        Args:
            treasury_address: Treasury address
            status: Optional status filter
            
        Returns:
            List of funding proposals
        """
        try:
            with self.lock:
                if status:
                    self.cursor.execute('''
                        SELECT * FROM funding_proposals 
                        WHERE treasury_address = ? AND status = ? 
                        ORDER BY submission_time DESC
                    ''', (treasury_address, status))
                else:
                    self.cursor.execute('''
                        SELECT * FROM funding_proposals 
                        WHERE treasury_address = ? 
                        ORDER BY submission_time DESC
                    ''', (treasury_address,))
                
                proposals = []
                for row in self.cursor.fetchall():
                    proposals.append({
                        'proposal_id': row['proposal_id'],
                        'treasury_address': row['treasury_address'],
                        'proposer_address': row['proposer_address'],
                        'title': row['title'],
                        'description': row['description'],
                        'amount': row['amount'],
                        'fee': row['fee'],
                        'recipient_address': row['recipient_address'],
                        'status': row['status'],
                        'submission_time': row['submission_time'],
                        'votes': json.loads(row['votes']),
                        'vote_count': row['vote_count'],
                        'vote_threshold': row['vote_threshold'],
                        'voting_period': row['voting_period'],
                        'finalized': bool(row['finalized'])
                    })
                
                return proposals
                
        except Exception as e:
            self.logger.error(f"Failed to get funding proposals: {e}")
            return []
    
    # Stats operations
    def set_stat(self, key: str, value: str):
        """
        Set statistic.
        
        Args:
            key: Statistic key
            value: Statistic value
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO stats (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                
                self.connection.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to set stat: {e}")
            self.connection.rollback()
            raise
    
    def get_stat(self, key: str) -> Optional[str]:
        """
        Get statistic.
        
        Args:
            key: Statistic key
            
        Returns:
            Statistic value or None
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT value FROM stats WHERE key = ?
                ''', (key,))
                
                row = self.cursor.fetchone()
                return row['value'] if row else None
                
        except Exception as e:
            self.logger.error(f"Failed to get stat: {e}")
            return None
    
    def get_all_stats(self) -> Dict:
        """
        Get all statistics.
        
        Returns:
            Dictionary of all statistics
        """
        try:
            with self.lock:
                self.cursor.execute('''
                    SELECT key, value FROM stats
                ''')
                
                stats = {}
                for row in self.cursor.fetchall():
                    stats[row['key']] = row['value']
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get all stats: {e}")
            return {}
    
    # Helper methods for row conversion
    def _row_to_block(self, row: sqlite3.Row) -> Dict:
        """Convert database row to block dictionary."""
        return {
            'block_index': row['block_index'],
            'previous_hash': row['previous_hash'],
            'block_hash': row['block_hash'],
            'merkle_root': row['merkle_root'],
            'timestamp': row['timestamp'],
            'difficulty': row['difficulty'],
            'nonce': row['nonce'],
            'transactions': json.loads(row['transactions']),
            'miner_address': row['miner_address'],
            'hash': row['hash']
        }
    
    def _row_to_transaction(self, row: sqlite3.Row) -> Dict:
        """Convert database row to transaction dictionary."""
        return {
            'transaction_id': row['transaction_id'],
            'sender': row['sender'],
            'recipient': row['recipient'],
            'amount': row['amount'],
            'fee': row['fee'],
            'timestamp': row['timestamp'],
            'data': json.loads(row['data']) if row['data'] else {},
            'signature': row['signature'],
            'block_index': row['block_index']
        }
    
    def _row_to_state(self, row: sqlite3.Row) -> Dict:
        """Convert database row to state dictionary."""
        return {
            'address': row['address'],
            'balance': row['balance'],
            'nonce': row['nonce'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    
    def _row_to_contract(self, row: sqlite3.Row) -> Dict:
        """Convert database row to contract dictionary."""
        return {
            'contract_address': row['contract_address'],
            'source_code': row['source_code'],
            'bytecode': row['bytecode'],
            'language': row['language'],
            'compiler_options': json.loads(row['compiler_options']) if row['compiler_options'] else {},
            'deployed_at': row['deployed_at'],
            'state': row['state'],
            'bytecode_hash': row['bytecode_hash'],
            'source_code_hash': row['source_code_hash'],
            'updated_at': row['updated_at'],
            'deactivated_at': row['deactivated_at'],
            'activated_at': row['activated_at'],
            'created_at': row['created_at']
        }
    
    def _row_to_wallet(self, row: sqlite3.Row) -> Dict:
        """Convert database row to wallet dictionary."""
        return {
            'address': row['address'],
            'public_key': row['public_key'],
            'private_key': row['private_key'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    
    def _row_to_node(self, row: sqlite3.Row) -> Dict:
        """Convert database row to node dictionary."""
        return {
            'node_id': row['node_id'],
            'address': row['address'],
            'port': row['port'],
            'last_seen': row['last_seen'],
            'is_connected': bool(row['is_connected']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    
    def _row_to_mempool_transaction(self, row: sqlite3.Row) -> Dict:
        """Convert database row to mempool transaction dictionary."""
        return {
            'transaction_id': row['transaction_id'],
            'sender': row['sender'],
            'recipient': row['recipient'],
            'amount': row['amount'],
            'fee': row['fee'],
            'timestamp': row['timestamp'],
            'data': json.loads(row['data']) if row['data'] else {},
            'signature': row['signature']
        }
    
    # Database management
    def backup(self, backup_path: str):
        """
        Backup database.
        
        Args:
            backup_path: Backup file path
        """
        try:
            import shutil
            
            self.connection.commit()
            shutil.copy2(self.db_path, backup_path)
            self.logger.debug(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise
    
    def restore(self, backup_path: str):
        """
        Restore database from backup.
        
        Args:
            backup_path: Backup file path
        """
        try:
            import shutil
            
            self.connection.close()
            shutil.copy2(backup_path, self.db_path)
            self._connect()
            self.logger.debug(f"Database restored from: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            raise
    
    def vacuum(self):
        """Optimize database."""
        try:
            with self.lock:
                self.cursor.execute('VACUUM')
                self.connection.commit()
                self.logger.debug("Database vacuumed")
                
        except Exception as e:
            self.logger.error(f"Vacuum failed: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.logger.debug("Database connection closed")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self):
        """String representation."""
        return f"Database(path={self.db_path})"
    
    def __str__(self):
        """String representation for printing."""
        try:
            block_count = self.get_block_count()
            transaction_count = len(self.get_all_transactions())
            contract_count = len(self.get_all_contracts())
            
            return (
                f"ChainForgeLedger Database\n"
                f"==========================\n"
                f"Path: {self.db_path}\n"
                f"Blocks: {block_count}\n"
                f"Transactions: {transaction_count}\n"
                f"Contracts: {contract_count}"
            )
            
        except Exception as e:
            return f"Database({self.db_path}) - Error: {e}"
