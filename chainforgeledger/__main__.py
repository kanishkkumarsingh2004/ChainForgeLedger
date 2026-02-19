#!/usr/bin/env python3
"""
ChainForgeLedger - Main CLI entry point

This module provides the command-line interface for the ChainForgeLedger blockchain platform.
"""

import sys
import argparse
import random
from chainforgeledger import Blockchain, Transaction, ProofOfWork, ProofOfStake, Tokenomics, Wallet, ValidatorManager, Validator


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ChainForgeLedger - Complete Blockchain Platform CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chainforgeledger --help          Show this help message
  chainforgeledger demo           Run comprehensive platform demonstration
  chainforgeledger basic          Run basic blockchain operations
  chainforgeledger pow --mine     Mine blocks with Proof of Work
  chainforgeledger pos --forge    Forge blocks with Proof of Stake
        """
    )
    
    subparsers = parser.add_subparsers(title='Commands', dest='command')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run comprehensive platform demonstration')
    
    # Basic command
    basic_parser = subparsers.add_parser('basic', help='Run basic blockchain operations')
    
    # PoW command
    pow_parser = subparsers.add_parser('pow', help='Proof of Work operations')
    pow_parser.add_argument('--mine', action='store_true', help='Mine a block')
    pow_parser.add_argument('--difficulty', type=int, default=3, help='Mining difficulty')
    
    # PoS command
    pos_parser = subparsers.add_parser('pos', help='Proof of Stake operations')
    pos_parser.add_argument('--forge', action='store_true', help='Forge a block')
    
    # Tokenomics command
    token_parser = subparsers.add_parser('token', help='Tokenomics operations')
    token_parser.add_argument('--create', action='store_true', help='Create tokenomics system')
    token_parser.add_argument('--mint', type=int, help='Mint tokens')
    token_parser.add_argument('--supply', type=int, default=1000000000, help='Total supply')
    
    args = parser.parse_args()
    
    if args.command == 'demo':
        run_comprehensive_demo()
    elif args.command == 'basic':
        run_basic_demo()
    elif args.command == 'pow':
        run_pow_operations(args)
    elif args.command == 'pos':
        run_pos_operations(args)
    elif args.command == 'token':
        run_token_operations(args)
    else:
        parser.print_help()
        return 1
        
    return 0


def run_basic_demo():
    """Run basic blockchain demonstration"""
    print("=== ChainForgeLedger - Basic Blockchain Operations ===")
    
    # Create blockchain with PoW
    print("\n1. Creating Proof of Work Blockchain...")
    blockchain = Blockchain()
    pow_consensus = ProofOfWork(blockchain, difficulty=2)
    print(f"   Genesis Block Created: {blockchain.chain[0].hash[:16]}...")
    
    # Create transactions
    print("\n2. Creating Transactions...")
    transactions = []
    for i in range(2):
        tx = Transaction(
            sender=f"user{100+i}",
            receiver=f"user{200+i}",
            amount=random.uniform(1, 100)
        )
        transactions.append(tx.to_dict())
        print(f"   Transaction {i+1} created: {tx.sender} -> {tx.receiver} ({tx.amount:.2f})")
    
    # Mine a block
    print("\n3. Mining Block...")
    block = pow_consensus.mine_block(transactions, "miner1")
    blockchain.add_block(block)
    print(f"   Block {block.index} mined")
    print(f"   Block Hash: {block.hash[:16]}...")
    print(f"   Transactions in Block: {len(block.transactions)}")
    
    # Verify blockchain
    print("\n4. Verifying Blockchain...")
    is_valid = blockchain.is_chain_valid()
    print(f"   Blockchain Valid: {'✅' if is_valid else '❌'}")
    
    print("\n=== Basic Demo Complete ===")


def run_comprehensive_demo():
    """Run comprehensive platform demonstration"""
    print("=== ChainForgeLedger - Comprehensive Platform Demonstration ===")
    
    # Create blockchain
    blockchain = Blockchain()
    pow_consensus = ProofOfWork(blockchain, difficulty=3)
    
    # Create transactions
    transactions = []
    for i in range(3):
        tx = Transaction(
            sender=f"user{100+i}",
            receiver=f"user{200+i}",
            amount=random.uniform(1, 100)
        )
        transactions.append(tx.to_dict())
    
    # Mine blocks
    for i in range(2):
        block = pow_consensus.mine_block(transactions, f"miner{i+1}")
        blockchain.add_block(block)
        print(f"Block {block.index} mined: {block.hash[:16]}...")
    
    print(f"Blockchain length: {len(blockchain.chain)} blocks")
    print(f"Total transactions: {sum(len(b.transactions) for b in blockchain.chain)}")
    print(f"Blockchain valid: {blockchain.is_chain_valid()}")
    
    print("\n=== Tokenomics System ===")
    tokenomics = Tokenomics(total_supply=1000000000)
    print(f"Total Supply: {tokenomics.total_supply:,}")
    print(f"Circulating Supply: {tokenomics.circulating_supply:,}")
    print(f"Staking Rewards Pool: {tokenomics.staking_rewards_pool:,}")
    
    print("\n=== Wallet System ===")
    wallet = Wallet()
    print(f"Wallet Address: {wallet.address}")
    print(f"Wallet Balance: {wallet.balance}")
    
    print("\n=== Comprehensive Demo Complete ===")


def run_pow_operations(args):
    """Run Proof of Work operations"""
    print("=== Proof of Work Operations ===")
    
    if args.mine:
        print(f"\nMining with difficulty: {args.difficulty}")
        blockchain = Blockchain(difficulty=args.difficulty)
        pow_consensus = ProofOfWork(blockchain, difficulty=args.difficulty)
        
        # Create transactions
        transactions = []
        for i in range(3):
            tx = Transaction(
                sender=f"user{100+i}",
                receiver=f"user{200+i}",
                amount=random.uniform(1, 100)
            )
            transactions.append(tx.to_dict())
        
        block = pow_consensus.mine_block(transactions, f"miner{args.difficulty}")
        blockchain.add_block(block)
        print(f"Block {block.index} mined")
        print(f"  Hash: {block.hash[:16]}...")
        print(f"  Nonce: {block.nonce}")
        print(f"  Transactions: {len(block.transactions)}")


def run_pos_operations(args):
    """Run Proof of Stake operations"""
    print("=== Proof of Stake Operations ===")
    
    if args.forge:
        # Create blockchain and validator manager
        blockchain = Blockchain()
        validator_manager = ValidatorManager()
        
        # Create initial validators
        initial_validators = [
            ("validator1", 500),
            ("validator2", 300),
            ("validator3", 200),
            ("validator4", 150)
        ]
        
        for name, stake in initial_validators:
            validator = Validator(name, stake)
            validator_manager.add_validator(validator)
        
        pos_consensus = ProofOfStake(blockchain, validator_manager)
        print(f"✓ Blockchain created with {len(pos_consensus.validator_manager.validators)} validators")
        
        # Create transactions
        transactions = []
        for i in range(2):
            tx = Transaction(
                sender=f"validator{i}",
                receiver=f"user{100+i}",
                amount=random.uniform(1, 100)
            )
            transactions.append(tx.to_dict())
        
        block = pos_consensus.forge_block(transactions)
        blockchain.add_block(block)
        print(f"Block {block.index} forged")
        print(f"  Hash: {block.hash[:16]}...")
        print(f"  Validator: {block.validator}")
        print(f"  Transactions: {len(block.transactions)}")


def run_token_operations(args):
    """Run tokenomics operations"""
    print("=== Tokenomics Operations ===")
    
    if args.create:
        tokenomics = Tokenomics(total_supply=args.supply)
        print(f"Tokenomics system created")
        print(f"  Total Supply: {tokenomics.total_supply:,}")
        print(f"  Circulating Supply: {tokenomics.current_supply:,}")
        print(f"  Staking Rewards Pool: {tokenomics.staking_rewards_pool:,}")
        
    if args.mint is not None:
        tokenomics = Tokenomics(total_supply=args.supply)
        tokenomics.mint_tokens(args.mint, 'staking_rewards')
        print(f"Successfully minted {args.mint:,} tokens")
        print(f"New Total Supply: {tokenomics.total_supply:,}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
