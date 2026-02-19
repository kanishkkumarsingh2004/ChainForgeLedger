"""
Comprehensive tests for ChainForgeLedger blockchain platform library
Testing all major components and functionality
"""

import unittest
from chainforgeledger import (
    Blockchain,
    Block,
    Transaction,
    ProofOfWork,
    ProofOfStake,
    Wallet,
    VirtualMachine,
    Compiler,
    ContractExecutor,
    Node,
    Peer,
    Protocol,
    MemPool,
    Proposal,
    VotingSystem,
    sha256_hash,
    keccak256_hash,
    generate_keys,
    KeyPair,
    MerkleTree,
    State,
    Validator,
    ValidatorManager,
    ApiServer,
    ApiRoutes,
    Database,
    BlockStorage,
    TransactionStorage,
    Tokenomics,
    Config,
    CrossChainBridge,
    StakingPool,
    LiquidityPool,
    FeeDistributionSystem,
    ForkHandler,
    ShardManager,
    StatePruner,
    LendingPool,
    BlockchainCache,
    DifficultyAdjuster,
    BlockSerializer,
    SlashingMechanism,
    ConsensusInterface,
    ProofOfWorkInterface,
    ProofOfStakeInterface,
    DelegatedProofOfStakeInterface,
    PBFTInterface,
    ConsensusFactory,
    ConsensusManager,
    MultiSignature,
    MultiSigWallet,
    MnemonicGenerator,
    KK20Token,
    KK721Token,
    TokenFactory,
    NativeCoin,
    Stablecoin,
    TreasuryManager,
    DAO,
    RateLimiter,
    ContractSandbox,
    LevelDBStorage,
    CryptoUtils,
    get_logger,
    configure_global_logger,
    LoggerMixin
)


class TestChainForgeLedgerComprehensive(unittest.TestCase):
    """Comprehensive test suite for ChainForgeLedger blockchain platform"""
    
    # ==================== Core Blockchain Tests ====================
    
    def test_blockchain_operations(self):
        """Test blockchain creation and basic operations"""
        blockchain = Blockchain(difficulty=2)
        self.assertEqual(len(blockchain.chain), 1)
        self.assertEqual(blockchain.chain[0].index, 0)
        
        # Test blockchain info
        info = blockchain.get_blockchain_info()
        self.assertIsNotNone(info)
        self.assertEqual(info["chain_length"], 1)
        self.assertEqual(info["difficulty"], 2)
        self.assertEqual(info["total_transactions"], 0)
        self.assertIsNotNone(info["last_block_hash"])
        self.assertTrue(info["is_valid"])
        
    def test_block_operations(self):
        """Test block creation and validation"""
        previous_block = Block(
            index=0,
            previous_hash="0" * 64,
            transactions=[],
            difficulty=2
        )
        
        block = Block(
            index=1,
            previous_hash=previous_block.hash,
            transactions=[],
            difficulty=2
        )
        
        self.assertIsNotNone(block)
        self.assertEqual(block.index, 1)
        self.assertEqual(block.previous_hash, previous_block.hash)
    
    def test_transaction_operations(self):
        """Test transaction creation and management"""
        tx = Transaction(
            sender="sender1",
            receiver="receiver1",
            amount=10.0
        )
        
        self.assertIsNotNone(tx)
        self.assertEqual(tx.sender, "sender1")
        self.assertEqual(tx.receiver, "receiver1")
        self.assertEqual(tx.amount, 10.0)
        
    def test_chain_validation(self):
        """Test blockchain chain validation"""
        blockchain = Blockchain(difficulty=2)
        self.assertTrue(blockchain.is_chain_valid())
        
        # Test block retrieval
        block_by_index = blockchain.get_block_by_index(0)
        self.assertIsNotNone(block_by_index)
        self.assertEqual(block_by_index.index, 0)
        
        genesis_block = blockchain.get_last_block()
        block_by_hash = blockchain.get_block_by_hash(genesis_block.hash)
        self.assertIsNotNone(block_by_hash)
        self.assertEqual(block_by_hash.index, 0)
    
    # ==================== Consensus Mechanisms ====================
    
    def test_pow_consensus(self):
        """Test Proof of Work consensus mechanism"""
        blockchain = Blockchain(difficulty=2)
        pow_consensus = ProofOfWork(blockchain, difficulty=2, reward=50.0)
        self.assertIsNotNone(pow_consensus)
        self.assertEqual(pow_consensus.difficulty, 2)
        self.assertEqual(pow_consensus.reward, 50.0)
    
    def test_pos_consensus(self):
        """Test Proof of Stake consensus mechanism"""
        blockchain = Blockchain(difficulty=2)
        validator_manager = ValidatorManager()
        pos_consensus = ProofOfStake(blockchain, validator_manager, reward=50.0)
        self.assertIsNotNone(pos_consensus)
    
    def test_validator_system(self):
        """Test validator management system"""
        validator_manager = ValidatorManager()
        validator = Validator("address1", stake=1000)
        validator_manager.add_validator(validator)
        
        self.assertEqual(len(validator_manager.validators), 1)
        self.assertIsNotNone(validator_manager.get_validator("address1"))
    
    # ==================== Cryptographic Tests ====================
    
    def test_wallet_operations(self):
        """Test wallet creation and management"""
        wallet = Wallet()
        self.assertIsNotNone(wallet.address)
        self.assertEqual(wallet.balance, 0.0)
    
    def test_key_generation(self):
        """Test cryptographic key generation"""
        key_pair, address = generate_keys()
        self.assertIsNotNone(key_pair)
        self.assertIsNotNone(address)
        self.assertIsInstance(key_pair, KeyPair)
    
    def test_hashing_functions(self):
        """Test SHA-256 hashing functionality"""
        test_data = "test data"
        hash_result = sha256_hash(test_data)
        self.assertIsNotNone(hash_result)
        self.assertEqual(len(hash_result), 64)
        self.assertIsInstance(hash_result, str)
        
        # Test hash consistency
        self.assertEqual(sha256_hash(test_data), hash_result)
    
    # ==================== Networking Tests ====================
    
    def test_node_operations(self):
        """Test network node creation and management"""
        node = Node("node1")
        self.assertIsNotNone(node)
        self.assertEqual(node.node_id, "node1")
    
    def test_peer_operations(self):
        """Test peer creation and management"""
        peer = Peer("peer1", "127.0.0.1", 8080)
        self.assertIsNotNone(peer)
        self.assertEqual(peer.address, "127.0.0.1")
        self.assertEqual(peer.port, 8080)
    
    def test_mempool_operations(self):
        """Test mempool operations"""
        mempool = MemPool()
        self.assertIsNotNone(mempool)
        
        # Test adding transactions (with signatures)
        tx1 = Transaction("sender1", "receiver1", 10.0)
        tx1.sign_transaction("private_key")
        tx2 = Transaction("sender2", "receiver2", 20.0)
        tx2.sign_transaction("private_key")
        
        mempool.add_transaction(tx1)
        mempool.add_transaction(tx2)
        
        self.assertEqual(len(mempool.transactions), 2)
    
    def test_protocol_operations(self):
        """Test network protocol operations"""
        protocol = Protocol()
        self.assertIsNotNone(protocol)
    
    # ==================== Smart Contracts Tests ====================
    
    def test_virtual_machine(self):
        """Test virtual machine operations"""
        vm = VirtualMachine()
        self.assertIsNotNone(vm)
    
    def test_compiler(self):
        """Test smart contract compiler"""
        compiler = Compiler()
        self.assertIsNotNone(compiler)
    
    def test_contract_executor(self):
        """Test contract executor operations"""
        executor = ContractExecutor()
        self.assertIsNotNone(executor)
    
    # ==================== Storage Tests ====================
    
    def test_database_operations(self):
        """Test database operations"""
        db = Database()
        self.assertIsNotNone(db)
    
    def test_block_storage(self):
        """Test block storage operations"""
        block_storage = BlockStorage()
        self.assertIsNotNone(block_storage)
    
    def test_transaction_storage(self):
        """Test transaction storage operations"""
        tx_storage = TransactionStorage()
        self.assertIsNotNone(tx_storage)
    
    # ==================== Governance Tests ====================
    
    def test_proposal_operations(self):
        """Test governance proposal creation and management"""
        proposal = Proposal(
            title="Test Proposal",
            description="This is a test proposal",
            proposer_address="user1"
        )
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.title, "Test Proposal")
    
    def test_voting_system(self):
        """Test voting system operations"""
        voting = VotingSystem()
        self.assertIsNotNone(voting)
    
    # ==================== Tokenomics Tests ====================
    
    def test_tokenomics_system(self):
        """Test tokenomics system operations"""
        tokenomics = Tokenomics()
        self.assertIsNotNone(tokenomics)
    
    # ==================== API Tests ====================
    
    def test_api_server(self):
        """Test API server operations"""
        server = ApiServer()
        self.assertIsNotNone(server)
    
    def test_api_routes(self):
        """Test API routes operations"""
        routes = ApiRoutes()
        self.assertIsNotNone(routes)
    
    # ==================== Utility Tests ====================
    
    def test_config_system(self):
        """Test configuration system"""
        config = Config()
        self.assertIsNotNone(config)
    
    def test_merkle_tree(self):
        """Test Merkle tree operations"""
        data = ["data1", "data2", "data3"]
        merkle_tree = MerkleTree(data)
        self.assertIsNotNone(merkle_tree)
        self.assertIsNotNone(merkle_tree.root)
    
    def test_state_management(self):
        """Test state management system"""
        state = State()
        self.assertIsNotNone(state)
    
    # ==================== Integration Tests ====================
    
    def test_blockchain_integration(self):
        """Test blockchain integration with transactions"""
        # Create blockchain
        blockchain = Blockchain(difficulty=2)
        
        # Create transactions
        tx1 = Transaction("sender1", "receiver1", 10.0)
        tx1.sign_transaction("private_key")
        tx2 = Transaction("sender2", "receiver2", 20.0)
        tx2.sign_transaction("private_key")
    
    def test_consensus_integration(self):
        """Test consensus mechanism integration"""
        blockchain = Blockchain(difficulty=2)
        pow_consensus = ProofOfWork(blockchain, difficulty=2, reward=50.0)
        self.assertIsNotNone(pow_consensus)
        
        # Test PoS integration
        validator_manager = ValidatorManager()
        validator = Validator("address1", stake=1000)
        validator_manager.add_validator(validator)
        pos_consensus = ProofOfStake(blockchain, validator_manager, reward=50.0)
        self.assertIsNotNone(pos_consensus)
    
    def test_wallet_transaction_integration(self):
        """Test wallet and transaction integration"""
        wallet1 = Wallet()
        wallet2 = Wallet()
        
        # Test transaction between wallets
        tx = Transaction(wallet1.address, wallet2.address, 10.0)
        self.assertIsNotNone(tx)
        self.assertEqual(tx.sender, wallet1.address)
        self.assertEqual(tx.receiver, wallet2.address)
        self.assertEqual(tx.amount, 10.0)
    
    def test_networking_integration(self):
        """Test networking components integration"""
        node1 = Node("node1")
        node2 = Node("node2")
        mempool = MemPool()
        
        # Connect nodes
        node1.connect(node2)
        self.assertEqual(len(node1.peers), 1)
        self.assertEqual(len(node2.peers), 1)
        
        # Add transaction to mempool
        tx = Transaction("sender1", "receiver1", 10.0)
        tx.sign_transaction("private_key")
        mempool.add_transaction(tx)
        self.assertEqual(len(mempool.transactions), 1)
    
    def test_smart_contract_integration(self):
        """Test smart contract components integration"""
        vm = VirtualMachine()
        compiler = Compiler()
        executor = ContractExecutor()
        
        self.assertIsNotNone(vm)
        self.assertIsNotNone(compiler)
        self.assertIsNotNone(executor)
    
    def test_storage_integration(self):
        """Test storage system integration"""
        db = Database()
        block_storage = BlockStorage()
        tx_storage = TransactionStorage()
        
        self.assertIsNotNone(db)
        self.assertIsNotNone(block_storage)
        self.assertIsNotNone(tx_storage)
    
    def test_governance_integration(self):
        """Test governance system integration"""
        proposal = Proposal(title="Test Proposal", description="Description", proposer_address="proposer1")
        voting = VotingSystem()
        
        self.assertIsNotNone(proposal)
        self.assertIsNotNone(voting)
    
    def test_tokenomics_integration(self):
        """Test tokenomics system integration"""
        tokenomics = Tokenomics()
        self.assertIsNotNone(tokenomics)
    
    # ==================== New Component Tests ====================
    
    def test_cross_chain_bridge(self):
        """Test cross-chain bridge functionality"""
        bridge = CrossChainBridge("chain1", "chain2")
        self.assertIsNotNone(bridge)
        self.assertEqual(bridge.source_chain, "chain1")
        self.assertEqual(bridge.destination_chain, "chain2")
    
    def test_staking_pool(self):
        """Test staking pool operations"""
        dao = DAO(
            name="Test DAO",
            description="Test DAO",
            creator_address="creator1",
            total_token_supply=1000000,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        treasury = TreasuryManager(dao)
        staking_pool = StakingPool(treasury)
        self.assertIsNotNone(staking_pool)
    
    def test_liquidity_pool(self):
        """Test liquidity pool operations"""
        liquidity_pool = LiquidityPool("TOKENA", "TOKENB")
        self.assertIsNotNone(liquidity_pool)
        self.assertEqual(liquidity_pool.token_a, "TOKENA")
        self.assertEqual(liquidity_pool.token_b, "TOKENB")
    
    def test_fee_distribution(self):
        """Test fee distribution system"""
        dao = DAO(
            name="Test DAO",
            description="Test DAO",
            creator_address="creator1",
            total_token_supply=1000000,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        treasury = TreasuryManager(dao)
        fee_distribution = FeeDistributionSystem(treasury)
        self.assertIsNotNone(fee_distribution)
    
    def test_fork_handler(self):
        """Test fork handler operations"""
        blockchain = Blockchain(difficulty=2)
        fork_handler = ForkHandler(blockchain)
        self.assertIsNotNone(fork_handler)
    
    def test_shard_manager(self):
        """Test shard manager operations"""
        shard_manager = ShardManager()
        self.assertIsNotNone(shard_manager)
    
    def test_state_pruner(self):
        """Test state pruner operations"""
        dao = DAO(
            name="Test DAO",
            description="Test DAO",
            creator_address="creator1",
            total_token_supply=1000000,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        treasury = TreasuryManager(dao)
        state_pruner = StatePruner("/tmp/test_storage", treasury)
        self.assertIsNotNone(state_pruner)
    
    def test_lending_pool(self):
        """Test lending pool operations"""
        lending_pool = LendingPool("TOKEN")
        self.assertIsNotNone(lending_pool)
        self.assertEqual(lending_pool.token, "TOKEN")
    
    def test_blockchain_cache(self):
        """Test blockchain cache operations"""
        blockchain_cache = BlockchainCache()
        self.assertIsNotNone(blockchain_cache)
    
    def test_difficulty_adjuster(self):
        """Test difficulty adjuster operations"""
        difficulty_adjuster = DifficultyAdjuster()
        self.assertIsNotNone(difficulty_adjuster)
    
    def test_block_serializer(self):
        """Test block serializer operations"""
        serializer = BlockSerializer()
        self.assertIsNotNone(serializer)
    
    def test_slashing_mechanism(self):
        """Test slashing mechanism operations"""
        slashing = SlashingMechanism()
        self.assertIsNotNone(slashing)
    
    def test_pow_interface(self):
        """Test Proof of Work consensus interface"""
        pow_interface = ProofOfWorkInterface(difficulty=2)
        self.assertIsNotNone(pow_interface)
        self.assertEqual(pow_interface.difficulty, 2)
    
    def test_pos_interface(self):
        """Test Proof of Stake consensus interface"""
        validator_manager = ValidatorManager()
        validator = Validator("validator1", stake=1000)
        validator_manager.add_validator(validator)
        pos_interface = ProofOfStakeInterface(validator_manager)
        self.assertIsNotNone(pos_interface)
    
    def test_consensus_factory(self):
        """Test consensus factory operations"""
        factory = ConsensusFactory()
        self.assertIsNotNone(factory)
    
    def test_consensus_manager(self):
        """Test consensus manager operations"""
        manager = ConsensusManager()
        self.assertIsNotNone(manager)
    
    def test_keccak256_hashing(self):
        """Test Keccak-256 hashing functionality"""
        test_data = "test data"
        hash_result = keccak256_hash(test_data)
        self.assertIsNotNone(hash_result)
        self.assertEqual(len(hash_result), 64)
        self.assertIsInstance(hash_result, str)
        
        # Test hash consistency
        self.assertEqual(keccak256_hash(test_data), hash_result)
    
    def test_multi_signature(self):
        """Test multi-signature operations"""
        multi_sig = MultiSignature(2, ["key1", "key2", "key3"])
        self.assertIsNotNone(multi_sig)
        self.assertEqual(multi_sig.required_signatures, 2)
        self.assertEqual(len(multi_sig.public_keys), 3)
    
    def test_multi_sig_wallet(self):
        """Test multi-signature wallet operations"""
        multi_sig_wallet = MultiSigWallet(2, ["key1", "key2", "key3"])
        self.assertIsNotNone(multi_sig_wallet)
    
    def test_mnemonic_generator(self):
        """Test mnemonic generator operations"""
        mnemonic_generator = MnemonicGenerator()
        self.assertIsNotNone(mnemonic_generator)
    
    def test_kk20_token(self):
        """Test KK20 token operations"""
        token = KK20Token("Test Token", "TTK", 18, 1000000)
        self.assertIsNotNone(token)
        self.assertEqual(token.name, "Test Token")
        self.assertEqual(token.symbol, "TTK")
        self.assertEqual(token.decimals, 18)
        self.assertEqual(token.total_supply, 1000000)
    
    def test_kk721_token(self):
        """Test KK721 token operations"""
        token = KK721Token("Test NFT", "TNFT")
        self.assertIsNotNone(token)
        self.assertEqual(token.name, "Test NFT")
        self.assertEqual(token.symbol, "TNFT")
    
    def test_token_factory(self):
        """Test token factory operations"""
        factory = TokenFactory()
        self.assertIsNotNone(factory)
    
    def test_native_coin(self):
        """Test native coin operations"""
        native_coin = NativeCoin()
        self.assertIsNotNone(native_coin)
    
    def test_stablecoin(self):
        """Test stablecoin operations"""
        stablecoin = Stablecoin("USD Stablecoin", "USDS", 1.0)
        self.assertIsNotNone(stablecoin)
        self.assertEqual(stablecoin.name, "USD Stablecoin")
        self.assertEqual(stablecoin.symbol, "USDS")
    
    def test_treasury_manager(self):
        """Test treasury manager operations"""
        dao = DAO(
            name="Test DAO",
            description="Test DAO",
            creator_address="creator1",
            total_token_supply=1000000,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        treasury = TreasuryManager(dao)
        self.assertIsNotNone(treasury)
    
    def test_dao_operations(self):
        """Test DAO operations"""
        dao = DAO(
            name="Test DAO",
            description="This is a test DAO",
            creator_address="creator1",
            total_token_supply=1000000,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        self.assertIsNotNone(dao)
        self.assertEqual(dao.name, "Test DAO")
    
    def test_rate_limiter(self):
        """Test rate limiter operations"""
        rate_limiter = RateLimiter()
        self.assertIsNotNone(rate_limiter)
    
    def test_contract_sandbox(self):
        """Test contract sandbox operations"""
        sandbox = ContractSandbox()
        self.assertIsNotNone(sandbox)
    
    def test_leveldb_storage(self):
        """Test LevelDB storage operations"""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as temp_dir:
            leveldb = LevelDBStorage(temp_dir)
            self.assertIsNotNone(leveldb)
    
    def test_crypto_utils(self):
        """Test crypto utilities operations"""
        self.assertIsNotNone(CryptoUtils)
    
    def test_logger_operations(self):
        """Test logger operations"""
        logger = get_logger("test_logger")
        self.assertIsNotNone(logger)
        
        configure_global_logger()
    
    # ==================== Enhanced Integration Tests ====================
    
    def test_comprehensive_platform_integration(self):
        """Test comprehensive platform integration with all components"""
        # Create blockchain and consensus
        blockchain = Blockchain(difficulty=2)
        validator_manager = ValidatorManager()
        validator = Validator("address1", stake=1000)
        validator_manager.add_validator(validator)
        pos_consensus = ProofOfStake(blockchain, validator_manager, reward=50.0)
        
        # Create wallets
        wallet1 = Wallet()
        wallet2 = Wallet()
        
        # Create network components
        node1 = Node("node1")
        node2 = Node("node2")
        node1.connect(node2)
        
        # Create tokenomics and DAO
        tokenomics = Tokenomics(total_supply=1000000000)
        dao = DAO(
            name="Test Platform DAO",
            description="Platform governance DAO",
            creator_address=wallet1.address,
            total_token_supply=tokenomics.total_supply,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
        
        # Verify all components are operational
        self.assertIsNotNone(blockchain)
        self.assertIsNotNone(pos_consensus)
        self.assertIsNotNone(wallet1)
        self.assertIsNotNone(wallet2)
        self.assertIsNotNone(node1)
        self.assertIsNotNone(node2)
        self.assertIsNotNone(tokenomics)
        self.assertIsNotNone(dao)


if __name__ == '__main__':
    print("Running ChainForgeLedger Comprehensive Tests...")
    print("=" * 60)
    
    # Run tests
    unittest.main()
