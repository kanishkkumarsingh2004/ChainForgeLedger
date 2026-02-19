"""
ChainForgeLedger - A complete blockchain platform library

A comprehensive blockchain platform built from scratch with pure Python.
Features include:
- Proof of Work (PoW) and Proof of Stake (PoS) consensus mechanisms
- Smart contract virtual machine with stack-based execution
- Decentralized exchange (DEX) with automated market making (AMM)
- Lending protocol with borrowing and lending functionality
- NFT marketplace for digital asset creation and trading
- Blockchain explorer for analytics and visualization
- Wallet system with various types (CLI, web, mobile, multisig, hardware)
- Governance system with DAO framework
- Security architecture with multiple protection mechanisms
- Tokenomics system with vesting, staking, and reward mechanisms
- Cross-chain bridge functionality
- Sharding support for scalability
- State pruning for storage optimization
- Caching layer for performance improvements

Author: Kanishk Kumar Singh
Email: kanishkkumar2004@gmail.com
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Kanishk Kumar Singh"
__email__ = "kanishkkumar2004@gmail.com"
__description__ = "A complete blockchain platform library with PoW/PoS consensus, smart contracts, and DeFi applications"

# Export core modules
from chainforgeledger.core.block import Block
from chainforgeledger.core.blockchain import Blockchain
from chainforgeledger.core.transaction import Transaction
from chainforgeledger.core.merkle import MerkleTree
from chainforgeledger.core.state import State
from chainforgeledger.core.bridge import CrossChainBridge
from chainforgeledger.core.staking import StakingPool
from chainforgeledger.core.liquidity import LiquidityPool
from chainforgeledger.core.fee_distribution import FeeDistributionSystem
from chainforgeledger.core.fork import ForkHandler
from chainforgeledger.core.sharding import ShardManager
from chainforgeledger.core.state_pruning import StatePruner
from chainforgeledger.core.lending import LendingPool
from chainforgeledger.core.caching import BlockchainCache
from chainforgeledger.core.difficulty import DifficultyAdjuster
from chainforgeledger.core.serialization import BlockSerializer

# Export consensus mechanisms
from chainforgeledger.consensus.pow import ProofOfWork
from chainforgeledger.consensus.pos import ProofOfStake
from chainforgeledger.consensus.validator import Validator, ValidatorManager
from chainforgeledger.consensus.slashing import SlashingMechanism
from chainforgeledger.consensus.interface import (
    ConsensusInterface,
    ProofOfWorkInterface,
    ProofOfStakeInterface,
    DelegatedProofOfStakeInterface,
    PBFTInterface,
    ConsensusFactory,
    ConsensusManager
)

# Export cryptographic utilities
from chainforgeledger.crypto.hashing import sha256_hash, keccak256_hash
from chainforgeledger.crypto.keys import generate_keys, KeyPair
from chainforgeledger.crypto.signature import Signature
from chainforgeledger.crypto.wallet import Wallet
from chainforgeledger.crypto.multisig import MultiSignature, MultiSigWallet
from chainforgeledger.crypto.mnemonic import MnemonicGenerator

# Export networking
from chainforgeledger.networking.node import Node
from chainforgeledger.networking.peer import Peer
from chainforgeledger.networking.protocol import Protocol
from chainforgeledger.networking.mempool import MemPool
from chainforgeledger.networking.rate_limiter import RateLimiter

# Export smart contracts
from chainforgeledger.smartcontracts.vm import VirtualMachine
from chainforgeledger.smartcontracts.compiler import Compiler
from chainforgeledger.smartcontracts.executor import ContractExecutor
from chainforgeledger.smartcontracts.sandbox import ContractSandbox

# Export tokenomics
from chainforgeledger.tokenomics import Tokenomics
from chainforgeledger.tokenomics.standards import KK20Token, KK721Token, TokenFactory
from chainforgeledger.tokenomics.native import NativeCoin
from chainforgeledger.tokenomics.stablecoin import Stablecoin
from chainforgeledger.tokenomics.treasury import TreasuryManager

# Export governance
from chainforgeledger.governance.proposal import Proposal
from chainforgeledger.governance.voting import VotingSystem
from chainforgeledger.governance.dao import DAO

# Export storage
from chainforgeledger.storage.database import Database
from chainforgeledger.storage.leveldb import LevelDBStorage
from chainforgeledger.storage.models import BlockStorage, TransactionStorage

# Export API
from chainforgeledger.api.server import ApiServer
from chainforgeledger.api.routes import ApiRoutes

# Export utilities
from chainforgeledger.utils.config import Config
from chainforgeledger.utils.crypto import CryptoUtils
from chainforgeledger.utils.logger import get_logger, configure_global_logger, LoggerMixin


__all__ = [
    # Core
    "Block", "Blockchain", "Transaction", "MerkleTree", "State", 
    "CrossChainBridge", "StakingPool", "LiquidityPool", "FeeDistributionSystem", 
    "ForkHandler", "ShardManager", "StatePruner", "LendingPool", 
    "BlockchainCache", "DifficultyAdjuster", "BlockSerializer",

    # Consensus
    "ProofOfWork", "ProofOfStake", "Validator", "ValidatorManager", 
    "SlashingMechanism", "ConsensusInterface", "ProofOfWorkInterface", 
    "ProofOfStakeInterface", "DelegatedProofOfStakeInterface", "PBFTInterface", 
    "ConsensusFactory", "ConsensusManager",

    # Crypto & Wallet
    "sha256_hash", "keccak256_hash", "generate_keys", "KeyPair", 
    "Signature", "Wallet", "MultiSignature", "MultiSigWallet", "MnemonicGenerator",

    # Networking
    "Node", "Peer", "Protocol", "MemPool", "RateLimiter",

    # Smart Contracts
    "VirtualMachine", "Compiler", "ContractExecutor", "ContractSandbox",

    # Storage & API
    "Database", "LevelDBStorage", "BlockStorage", "TransactionStorage",
    "ApiServer", "ApiRoutes",

    # Governance & Tokenomics
    "Proposal", "VotingSystem", "DAO", "Tokenomics", "KK20Token", 
    "KK721Token", "TokenFactory", "NativeCoin", "Stablecoin", "TreasuryManager",

    # Utilities
    "Config", "CryptoUtils", "get_logger", "configure_global_logger", "LoggerMixin"
]