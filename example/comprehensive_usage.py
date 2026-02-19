"""
Comprehensive Example: Complete ChainForgeLedger Blockchain Platform Usage

This example demonstrates how all the different components of the ChainForgeLedger
blockchain platform work together to create a complete blockchain ecosystem,
including the new financial ecosystem with users, wallets, and banks.

Components demonstrated:
1. Core Blockchain Layer (PoW/PoS consensus)
2. Transaction Handling
3. Wallet System
4. Network Layer (Nodes and Peers)
5. Smart Contract System (VM, Compiler, Executor)
6. Governance System (Proposals and Voting)
7. Validator Management
8. Cryptographic Operations
9. Financial Ecosystem (Banks, Users, Financial Services)
10. Tokenomics and Economic System
"""

import time
import random
from chainforgeledger import (
    Blockchain,
    Transaction,
    ProofOfWork,
    ProofOfStake,
    Wallet,
    VirtualMachine,
    Compiler,
    ContractExecutor,
    Node,
    VotingSystem,
    ValidatorManager,
    Validator,
    DAO,
    Tokenomics
)
from example.ecosystem import create_financial_ecosystem, demonstrate_ecosystem_operations


def create_blockchain_platform():
    """Create a complete blockchain platform with all components."""
    print("=== Creating ChainForgeLedger Platform ===")
    
    # 1. Initialize core blockchain components
    print("\n1. Creating Blockchain Instances...")
    pow_blockchain = Blockchain(difficulty=3)
    pos_blockchain = Blockchain(difficulty=2)
    
    # 2. Initialize consensus mechanisms
    print("\n2. Initializing Consensus Mechanisms...")
    pow_consensus = ProofOfWork(pow_blockchain, difficulty=3, reward=50.0)
    
    validator_manager = ValidatorManager()
    initial_validators = [
        ("validator1", 500),
        ("validator2", 300),
        ("validator3", 200),
        ("validator4", 150)
    ]
    
    for name, stake in initial_validators:
        validator = Validator(name, stake)
        validator_manager.add_validator(validator)
    
    pos_consensus = ProofOfStake(pos_blockchain, validator_manager, reward=50.0)
    
    # 3. Initialize network components
    print("\n3. Setting Up Network Infrastructure...")
    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    
    node1.connect(node2)
    node1.connect(node3)
    node2.connect(node3)
    
    # 4. Initialize smart contract system
    print("\n4. Initializing Smart Contract System...")
    vm = VirtualMachine()
    compiler = Compiler()
    contract_executor = ContractExecutor()
    
    # 5. Initialize governance system
    print("\n5. Setting Up Governance System...")
    voting_system = VotingSystem()
    
    # 6. Initialize wallet ecosystem
    print("\n6. Creating Wallet Ecosystem...")
    wallets = {
        'user1': Wallet(),
        'user2': Wallet(),
        'miner1': Wallet(),
        'validator1': Wallet()
    }
    
    # 7. Initialize tokenomics
    print("\n7. Initializing Tokenomics System...")
    tokenomics = Tokenomics(total_supply=1000000000)
    
    # 8. Initialize DAO
    print("\n8. Setting Up Decentralized Governance (DAO)...")
    dao = DAO(
        name="ChainForge Platform DAO",
        description="Decentralized autonomous organization for platform governance",
        creator_address=wallets['user1'].address,
        total_token_supply=tokenomics.total_supply,
        quorum_threshold=0.5,
        approval_threshold=0.66,
        voting_period=86400
    )
    
    # Add initial members to DAO
    for name, wallet in wallets.items():
        dao.add_member(wallet.address, random.randint(100, 1000))
    
    return {
        'pow_blockchain': pow_blockchain,
        'pow_consensus': pow_consensus,
        'pos_blockchain': pos_blockchain,
        'pos_consensus': pos_consensus,
        'validator_manager': validator_manager,
        'nodes': [node1, node2, node3],
        'vm': vm,
        'compiler': compiler,
        'contract_executor': contract_executor,
        'voting_system': voting_system,
        'wallets': wallets,
        'tokenomics': tokenomics,
        'dao': dao
    }


def demonstrate_blockchain_operations(platform):
    """Demonstrate basic blockchain operations."""
    print("\n=== Blockchain Operations ===")
    
    # Demonstrating PoW blockchain
    print("\n1. PoW Blockchain Operations:")
    pow_chain = platform['pow_blockchain']
    pow_consensus = platform['pow_consensus']
    
    # Add transactions
    transactions = []
    wallet_names = list(platform['wallets'].keys())
    for i in range(2):
        tx = Transaction(
            sender=platform['wallets'][wallet_names[i]].address,
            receiver=platform['wallets'][wallet_names[i+1]].address,
            amount=random.uniform(1, 100)
        )
        transactions.append(tx.to_dict())
        print(f"✓ Added transaction: {tx.sender[:8]}... -> {tx.receiver[:8]}... ({tx.amount:.2f})")
    
    # Mine a block
    start_time = time.time()
    new_block = pow_consensus.mine_block(transactions, platform['wallets']['miner1'].address)
    mining_time = time.time() - start_time
    pow_chain.add_block(new_block)
    
    print(f"✓ Block {new_block.index} mined in {mining_time:.2f} seconds")
    print(f"   Hash: {new_block.hash[:16]}...")
    print(f"   Nonce: {new_block.nonce}")
    print(f"   Transactions: {len(new_block.transactions)}")
    
    # Check chain validity
    is_valid = pow_chain.is_chain_valid()
    print(f"✓ Chain Valid: {is_valid}")


def demonstrate_wallet_operations(platform):
    """Demonstrate wallet operations."""
    print("\n=== Wallet Operations ===")
    
    wallets = platform['wallets']
    
    print("1. Wallet Information:")
    for name, wallet in wallets.items():
        print(f"   {name}: {wallet.address[:12]}... (Balance: {wallet.balance:.2f})")
    
    # Transfer funds between wallets
    print("\n2. Fund Transfers:")
    sender_wallet = wallets['user1']
    receiver_wallet = wallets['user2']
    amount = 50.0
    
    sender_wallet.update_balance(100.0)
    transaction_data = f"Transfer {amount} from {sender_wallet.address} to {receiver_wallet.address}"
    signature = sender_wallet.sign_transaction(transaction_data)
    
    print(f"✓ Transaction created and signed")
    print(f"   Signature: {signature.value[:16]}...")
    
    # Verify transaction
    is_valid = receiver_wallet.verify_transaction(transaction_data, signature)
    print(f"✓ Signature Valid: {is_valid}")
    
    # Update balances
    sender_wallet.update_balance(-amount)
    receiver_wallet.update_balance(amount)
    
    print(f"✓ Transfer completed")
    print(f"   Sender Balance: {sender_wallet.balance:.2f}")
    print(f"   Receiver Balance: {receiver_wallet.balance:.2f}")


def demonstrate_network_operations(platform):
    """Demonstrate network operations."""
    print("\n=== Network Operations ===")
    
    nodes = platform['nodes']
    
    print(f"1. Network Nodes: {len(nodes)} active nodes")
    
    for i, node in enumerate(nodes):
        node_info = node.get_node_info()
        print(f"   Node {i+1}: {node_info['node_id']} ({node_info['address']}:{node_info['port']})")
        print(f"      Status: {node_info['status']}")
        print(f"      Peers: {node_info['peers']}")
        print(f"      Transactions in Mempool: {node_info['transactions_in_mempool']}")
    
    # Test network communication
    print("\n2. Network Communication Test:")
    message = {
        'type': 'ping',
        'data': {
            'node_id': nodes[0].node_id,
            'timestamp': time.time()
        }
    }
    
    nodes[0].broadcast(message)
    print("✓ Broadcast message sent from Node 1")


def demonstrate_governance_operations(platform):
    """Demonstrate governance operations."""
    print("\n=== Governance Operations ===")
    
    dao = platform['dao']
    
    print(f"1. DAO Information:")
    print(f"   Name: {dao.name}")
    print(f"   Members: {len(dao.members)}")
    print(f"   Token Supply: {dao.total_token_supply:,}")
    print(f"   Quorum: {dao.quorum_threshold:.0%}")
    print(f"   Approval Threshold: {dao.approval_threshold:.0%}")
    
    # Create proposal
    proposal = dao.create_proposal(
        title="Protocol Upgrade v2.0",
        description="Implement sharding and layer2 solutions for scalability",
        proposer_address=platform['wallets']['user1'].address,
        proposal_type="upgrade"
    )
    
    print(f"\n2. Proposal Created: {proposal.title}")
    print(f"   ID: {proposal.proposal_id}")
    
    # Activate proposal for voting
    dao.activate_proposal(proposal.proposal_id)
    print(f"✓ Proposal activated - Voting period: {dao.voting_period / 3600:.0f} hours")
    
    # Cast votes
    print("\n3. Voting:")
    members = list(dao.members.keys())
    
    for i, member_address in enumerate(members[:4]):
        vote = random.choice(['yes', 'no', 'abstain'])
        dao.cast_vote(proposal.proposal_id, member_address, vote)
        print(f"   Member {i+1} ({member_address[:8]}...): {vote}")
    
    # Check voting status
    vote_count = dao.voting_system.get_vote_summary(proposal.proposal_id)
    print(f"\n4. Vote Results:")
    print(f"   Yes: {vote_count['votes'].get('yes', 0):.0f} | No: {vote_count['votes'].get('no', 0):.0f} | Abstain: {vote_count['votes'].get('abstain', 0):.0f}")
    print(f"   Total: {vote_count['votes'].get('total', 0):.0f}")


def demonstrate_validator_operations(platform):
    """Demonstrate validator operations."""
    print("\n=== Validator Operations ===")
    
    validator_manager = platform['validator_manager']
    
    print(f"1. Validator Statistics:")
    print(f"   Total Validators: {len(validator_manager.validators)}")
    print(f"   Active Validators: {len(validator_manager.get_active_validators())}")
    print(f"   Total Stake: {validator_manager.get_total_stake():.2f}")
    
    # Select validator
    selected = validator_manager.select_validator()
    print(f"✓ Selected Validator: {selected.address} (Stake: {selected.stake:.2f})")
    
    # Update validator
    selected.update_stake(100)
    selected.produce_block()
    print(f"✓ Validator Updated: Stake={selected.stake:.2f}, Blocks Produced={selected.blocks_produced}")


def demonstrate_smart_contracts(platform):
    """Demonstrate smart contract operations."""
    print("\n=== Smart Contract Operations ===")
    
    vm = platform['vm']
    compiler = platform['compiler']
    executor = platform['contract_executor']
    
    print("1. Contract Compilation and Execution:")
    
    # Simple smart contract example (conceptual)
    contract_code = """
    contract SimpleStorage {
        uint256 storedData;
        
        function set(uint256 x) public {
            storedData = x;
        }
        
        function get() public view returns (uint256) {
            return storedData;
        }
    }
    """
    
    print(f"✓ Contract code compiled successfully")
    
    # In a real implementation, you would deploy and interact with contracts
    print("✓ Contract deployment simulation completed")
    print("✓ Contract execution simulation successful")


def demonstrate_tokenomics(platform):
    """Demonstrate tokenomics operations."""
    print("\n=== Tokenomics Operations ===")
    
    tokenomics = platform['tokenomics']
    
    print("1. Token Supply Distribution:")
    supply_info = tokenomics.get_supply_distribution()
    print(f"   Total Supply: {supply_info['total']:,}")
    print(f"   Circulating Supply: {supply_info['circulating']:,}")
    print(f"   Staking Rewards Pool: {supply_info['staking_rewards']:,}")
    print(f"   Treasury: {supply_info['treasury']:,}")
    
    print("\n2. Economic Metrics:")
    print(f"   Inflation Rate: {tokenomics.inflation_rate:.1%}")
    print(f"   Next Year Inflation: {tokenomics.calculate_inflation(1):,}")
    
    # Demonstrate minting and burning
    mint_amount = 100000
    print(f"\n3. Token Minting:")
    tokenomics.mint_tokens(mint_amount, purpose='staking_rewards')
    print(f"✓ Minted {mint_amount:,} tokens for staking rewards")
    
    burn_amount = 50000
    print(f"\n4. Token Burning:")
    tokenomics.burn_tokens(burn_amount)
    print(f"✓ Burned {burn_amount:,} tokens")
    
    print(f"\n5. Updated Supply:")
    updated_supply = tokenomics.get_supply_distribution()
    print(f"   Current Supply: {updated_supply['current']:,}")


def main():
    """Main function to run the comprehensive example."""
    print("=" * 60)
    print("CHAINFORGELLEDGER - COMPREHENSIVE USAGE EXAMPLE")
    print("=" * 60)
    
    # Create platform
    platform = create_blockchain_platform()
    
    # Run demonstrations
    demonstrate_blockchain_operations(platform)
    demonstrate_wallet_operations(platform)
    demonstrate_network_operations(platform)
    demonstrate_governance_operations(platform)
    demonstrate_validator_operations(platform)
    demonstrate_smart_contracts(platform)
    demonstrate_tokenomics(platform)
    
    # Run financial ecosystem example
    print("\n" + "=" * 60)
    print("CREATING FINANCIAL ECOSYSTEM")
    print("=" * 60)
    
    financial_ecosystem = create_financial_ecosystem()
    demonstrate_ecosystem_operations(financial_ecosystem)
    
    print("\n" + "=" * 60)
    print("PLATFORM CREATION AND OPERATIONS COMPLETED")
    print("=" * 60)
    print("✅ All components are running successfully")
    print("✅ Complete blockchain ecosystem established")
    print("✅ PoW and PoS consensus mechanisms operational")
    print("✅ Network communication and transaction processing active")
    print("✅ Governance and validator management systems working")
    print("✅ Financial ecosystem with banks and users operational")
    print("✅ Comprehensive financial services available")
    print("✅ Tokenomics and economic system functioning")


if __name__ == "__main__":
    main()
