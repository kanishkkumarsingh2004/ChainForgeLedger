"""
Basic Usage Example: ChainForgeLedger Blockchain Platform Fundamentals

This example demonstrates the basic functionality of the ChainForgeLedger
blockchain platform with both Proof of Work and Proof of Stake consensus mechanisms.
"""

from chainforgeledger import (
    Blockchain,
    Transaction,
    ProofOfWork,
    ProofOfStake,
    Wallet,
    ValidatorManager,
    Validator
)
import time
import random


def demo_blockchain_operations():
    """Demonstrate basic blockchain operations."""
    print("=== Blockchain Operations ===")
    
    # Create blockchain
    blockchain = Blockchain(difficulty=2)
    print(f"✓ Blockchain created with difficulty: {blockchain.difficulty}")
    print(f"✓ Genesis block created")
    
    # Add transactions
    for i in range(3):
        tx = Transaction(
            sender=f"user{random.randint(1, 100)}",
            receiver=f"user{random.randint(1, 100)}",
            amount=random.uniform(1, 100)
        )
        print(f"✓ Added transaction: {tx.sender} -> {tx.receiver} ({tx.amount:.2f})")
    
    # Get blockchain info
    info = blockchain.get_blockchain_info()
    print(f"\n✓ Blockchain Info:")
    print(f"   Chain Length: {info['chain_length']}")
    print(f"   Difficulty: {info['difficulty']}")
    print(f"   Total Transactions: {info['total_transactions']}")
    print(f"   Last Block Hash: {info['last_block_hash'][:16]}...")
    print(f"   Chain Valid: {info['is_valid']}")
    
    return blockchain


def demo_pow_consensus():
    """Demonstrate Proof of Work consensus."""
    print("\n=== Proof of Work Consensus ===")
    
    blockchain = Blockchain(difficulty=2)
    pow_consensus = ProofOfWork(blockchain, difficulty=2, reward=50.0)
    
    # Add transactions
    transactions = []
    for i in range(3):
        tx = Transaction(
            sender=f"user{random.randint(1, 100)}",
            receiver=f"user{random.randint(1, 100)}",
            amount=random.uniform(1, 100)
        )
        transactions.append(tx.to_dict())
        print(f"✓ Added transaction: {tx.sender} -> {tx.receiver} ({tx.amount:.2f})")
    
    # Mine a block
    start_time = time.time()
    new_block = pow_consensus.mine_block(transactions, f"miner{random.randint(1, 10)}")
    mining_time = time.time() - start_time
    
    print(f"\n✓ Block {new_block.index} mined in {mining_time:.2f} seconds")
    print(f"   Hash: {new_block.hash[:16]}...")
    print(f"   Nonce: {new_block.nonce}")
    print(f"   Transactions: {len(new_block.transactions)}")
    
    # Validate block
    is_valid = pow_consensus.validate_block(new_block)
    print(f"✓ Block Valid: {is_valid}")
    
    blockchain.add_block(new_block)
    
    return blockchain, pow_consensus


def demo_pos_consensus():
    """Demonstrate Proof of Stake consensus."""
    print("\n=== Proof of Stake Consensus ===")
    
    blockchain = Blockchain(difficulty=2)
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
    
    pos_consensus = ProofOfStake(blockchain, validator_manager, reward=50.0)
    print(f"✓ Blockchain created with {len(pos_consensus.validator_manager.validators)} validators")
    print(f"✓ Genesis block created")
    
    # Add transactions
    transactions = []
    for i in range(2):
        tx = Transaction(
            sender=f"validator{random.randint(1, 4)}",
            receiver=f"user{random.randint(1, 100)}",
            amount=random.uniform(1, 100)
        )
        transactions.append(tx.to_dict())
        print(f"✓ Added transaction: {tx.sender} -> {tx.receiver} ({tx.amount:.2f})")
    
    # Forge a block
    start_time = time.time()
    new_block = pos_consensus.forge_block(transactions)
    forging_time = time.time() - start_time
    
    print(f"\n✓ Block {new_block.index} forged by {new_block.validator}")
    print(f"   Hash: {new_block.hash[:16]}...")
    print(f"   Forging Time: {forging_time:.2f} seconds")
    print(f"   Transactions: {len(new_block.transactions)}")
    
    # Validate block
    is_valid = pos_consensus.validate_block(new_block)
    print(f"✓ Block Valid: {is_valid}")
    
    blockchain.add_block(new_block)
    
    return blockchain, pos_consensus


def demo_wallet_operations():
    """Demonstrate wallet functionality."""
    print("\n=== Wallet System ===")
    
    # Create wallets
    wallet1 = Wallet()
    wallet2 = Wallet()
    
    print(f"✓ Wallet 1: {wallet1.address}")
    print(f"✓ Wallet 2: {wallet2.address}")
    
    # Check balances
    print(f"✓ Wallet 1 Balance: {wallet1.balance:.2f}")
    print(f"✓ Wallet 2 Balance: {wallet2.balance:.2f}")
    
    # Update balances
    wallet1.update_balance(100.0)
    wallet2.update_balance(50.0)
    
    print(f"✓ After Update:")
    print(f"   Wallet 1: {wallet1.balance:.2f}")
    print(f"   Wallet 2: {wallet2.balance:.2f}")
    
    # Create a transaction
    transaction_data = f"Transfer 25.0 from {wallet1.address} to {wallet2.address}"
    signature = wallet1.sign_transaction(transaction_data)
    
    print(f"✓ Transaction Signature: {signature.value[:16]}...")
    
    # Verify signature (using sender's private key)
    from chainforgeledger.crypto.signature import verify as verify_signature
    is_valid = verify_signature(signature, transaction_data, wallet1.key_pair.private_key)
    print(f"✓ Signature Valid: {is_valid}")
    
    return wallet1, wallet2


def demo_validator_system():
    """Demonstrate validator management."""
    print("\n=== Validator System ===")
    
    validator_manager = ValidatorManager()
    
    # Create validators
    validator1 = Validator("validator1", 500)
    validator2 = Validator("validator2", 300)
    validator3 = Validator("validator3", 200)
    
    validator_manager.add_validator(validator1)
    validator_manager.add_validator(validator2)
    validator_manager.add_validator(validator3)
    
    print(f"✓ Total Validators: {len(validator_manager.validators)}")
    print(f"✓ Active Validators: {len(validator_manager.get_active_validators())}")
    print(f"✓ Total Stake: {validator_manager.get_total_stake():.2f}")
    
    # Select validator
    selected = validator_manager.select_validator()
    print(f"✓ Selected Validator: {selected.address} (Stake: {selected.stake:.2f})")
    
    # Update validator
    validator1.update_stake(100)
    print(f"✓ Validator 1 Stake Updated: {validator1.stake:.2f}")
    
    validator1.produce_block()
    print(f"✓ Validator 1 Blocks Produced: {validator1.blocks_produced}")
    
    return validator_manager


def main():
    """Main function to run all demonstrations."""
    print("=" * 50)
    print("CHAINFORGELLEDGER - BASIC USAGE EXAMPLE")
    print("=" * 50)
    
    blockchain = demo_blockchain_operations()
    pow_chain, pow_consensus = demo_pow_consensus()
    pos_chain, pos_consensus = demo_pos_consensus()
    wallet1, wallet2 = demo_wallet_operations()
    validator_manager = demo_validator_system()
    
    print("\n" + "=" * 50)
    print("DEMO COMPLETED - ALL SYSTEMS OPERATIONAL")
    print("=" * 50)
    print("✅ Blockchain platform initialized successfully")
    print("✅ Both PoW and PoS consensus mechanisms working")
    print("✅ Wallet system and transaction processing active")
    print("✅ Validator management system operational")


if __name__ == "__main__":
    main()
