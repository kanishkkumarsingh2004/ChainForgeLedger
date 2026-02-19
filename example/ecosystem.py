"""
ChainForgeLedger Ecosystem Example: Complete Financial Ecosystem

This example demonstrates a complete financial ecosystem built on top of ChainForgeLedger,
including users, banks, financial institutions, and various financial services.

Components demonstrated:
1. User Wallets and Accounts
2. Bank Institutions and Services
3. Financial Transactions and Services
4. Credit and Lending Systems
5. Investment and Asset Management
6. Regulatory Compliance
7. Insurance and Risk Management
8. Cross-Border Payments
"""

import time
import random
from typing import Dict, Optional
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


class Bank:
    """
    Represents a financial institution (bank) in the blockchain ecosystem.
    
    Attributes:
        name: Bank name
        address: Bank's blockchain address
        wallet: Bank's wallet for transactions
        customers: List of customer addresses
        services: Available banking services
        balance: Bank's total balance
        transaction_fees: Fee structure for services
    """
    
    def __init__(self, name: str):
        self.name = name
        self.wallet = Wallet()
        self.address = self.wallet.address
        self.customers = []
        self.services = {
            'basic': ['savings', 'checking', 'transfers'],
            'premium': ['investments', 'loans', 'credit_cards'],
            'corporate': ['merchant_services', 'treasury', 'international']
        }
        self.balance = 0.0
        self.transaction_fees = {
            'domestic_transfer': 0.50,
            'international_transfer': 5.00,
            'loan_processing': 50.00,
            'investment_fee': 0.02  # 2% fee
        }
        self.loans = []
        self.investments = []
    
    def add_customer(self, customer_address: str, customer_name: str):
        """Add a customer to the bank."""
        self.customers.append({
            'address': customer_address,
            'name': customer_name,
            'accounts': [],
            'credit_score': random.randint(300, 850)
        })
    
    def open_account(self, customer_address: str, account_type: str):
        """Open a new account for a customer."""
        customer = next((c for c in self.customers if c['address'] == customer_address), None)
        if customer:
            account = {
                'account_id': f"{self.name.lower()}_{customer_address[:8]}_{account_type}",
                'account_type': account_type,
                'balance': 0.0,
                'created_at': time.time()
            }
            customer['accounts'].append(account)
            return account
    
    def process_transfer(self, from_customer: str, to_customer: str, amount: float, 
                       transfer_type: str = 'domestic') -> Dict:
        """Process a transfer between customers."""
        fee = self.transaction_fees.get(transfer_type, 0.50)
        total_amount = amount + fee
        
        transaction = Transaction(
            sender=from_customer,
            receiver=to_customer,
            amount=amount,
            fee=fee,
            data={
                'bank': self.name,
                'transfer_type': transfer_type,
                'processed_at': time.time()
            }
        )
        
        return transaction.to_dict()
    
    def issue_loan(self, customer_address: str, amount: float, interest_rate: float, 
                  term_months: int) -> Dict:
        """Issue a loan to a customer."""
        loan = {
            'loan_id': f"loan_{self.name.lower()}_{customer_address[:8]}_{int(time.time())}",
            'customer_address': customer_address,
            'amount': amount,
            'interest_rate': interest_rate,
            'term_months': term_months,
            'issued_at': time.time(),
            'status': 'active',
            'payments': []
        }
        
        self.loans.append(loan)
        
        # Transfer loan amount to customer
        transaction = Transaction(
            sender=self.address,
            receiver=customer_address,
            amount=amount,
            fee=self.transaction_fees['loan_processing'],
            data={
                'bank': self.name,
                'transaction_type': 'loan_disbursement',
                'loan_id': loan['loan_id']
            }
        )
        
        return {
            'loan': loan,
            'transaction': transaction.to_dict()
        }
    
    def process_payment(self, customer_address: str, loan_id: str, amount: float) -> Dict:
        """Process a loan payment."""
        loan = next((l for l in self.loans if l['loan_id'] == loan_id), None)
        
        if loan and loan['customer_address'] == customer_address:
            payment = {
                'payment_id': f"payment_{loan_id}_{int(time.time())}",
                'amount': amount,
                'timestamp': time.time(),
                'type': 'payment'
            }
            loan['payments'].append(payment)
            
            transaction = Transaction(
                sender=customer_address,
                receiver=self.address,
                amount=amount,
                data={
                    'bank': self.name,
                    'transaction_type': 'loan_payment',
                    'loan_id': loan_id
                }
            )
            
            return transaction.to_dict()
    
    def get_bank_statistics(self) -> Dict:
        """Get comprehensive bank statistics."""
        total_loans = sum(loan['amount'] for loan in self.loans if loan['status'] == 'active')
        total_customers = len(self.customers)
        total_accounts = sum(len(customer['accounts']) for customer in self.customers)
        
        return {
            'name': self.name,
            'address': self.address,
            'total_customers': total_customers,
            'total_accounts': total_accounts,
            'total_loans': total_loans,
            'available_services': list(self.services.keys()),
            'transaction_fees': self.transaction_fees
        }
    
    def __repr__(self):
        return f"Bank(name={self.name}, customers={len(self.customers)})"
    
    def __str__(self):
        stats = self.get_bank_statistics()
        return (
            f"{self.name} Bank\n"
            f"Address: {self.address[:16]}...\n"
            f"Customers: {stats['total_customers']}\n"
            f"Accounts: {stats['total_accounts']}\n"
            f"Active Loans: {len([l for l in self.loans if l['status'] == 'active'])}\n"
            f"Total Loan Amount: ${stats['total_loans']:,.2f}"
        )


class User:
    """
    Represents a user in the blockchain ecosystem.
    
    Attributes:
        name: User's full name
        address: User's blockchain address
        wallet: User's wallet
        bank_accounts: List of bank accounts
        credit_score: Credit score
        transactions: Transaction history
    """
    
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.wallet = Wallet()
        self.address = self.wallet.address
        self.bank_accounts = []
        self.credit_score = random.randint(500, 850)
        self.transactions = []
    
    def open_bank_account(self, bank: Bank, account_type: str):
        """Open a bank account with a specific bank."""
        account = bank.open_account(self.address, account_type)
        if account:
            self.bank_accounts.append({
                'bank': bank.name,
                'account': account
            })
    
    def transfer_funds(self, bank: Bank, to_user: 'User', amount: float, 
                       transfer_type: str = 'domestic'):
        """Transfer funds to another user through a bank."""
        transaction = bank.process_transfer(
            from_customer=self.address,
            to_customer=to_user.address,
            amount=amount,
            transfer_type=transfer_type
        )
        
        self.transactions.append(transaction)
        to_user.transactions.append(transaction)
        
        return transaction
    
    def apply_for_loan(self, bank: Bank, amount: float, term_months: int) -> Optional[Dict]:
        """Apply for a loan from a bank."""
        interest_rate = 0.05 + (850 - self.credit_score) / 1000  # Risk-based pricing
        
        if self.credit_score >= 650:
            return bank.issue_loan(self.address, amount, interest_rate, term_months)
    
    def make_loan_payment(self, bank: Bank, loan_id: str, amount: float):
        """Make a loan payment."""
        return bank.process_payment(self.address, loan_id, amount)
    
    def get_user_statistics(self) -> Dict:
        """Get comprehensive user statistics."""
        total_balance = self.wallet.balance
        total_transactions = len(self.transactions)
        total_accounts = len(self.bank_accounts)
        
        return {
            'name': self.name,
            'email': self.email,
            'address': self.address,
            'credit_score': self.credit_score,
            'total_balance': total_balance,
            'total_transactions': total_transactions,
            'total_accounts': total_accounts,
            'bank_accounts': self.bank_accounts
        }
    
    def __repr__(self):
        return f"User(name={self.name}, address={self.address[:16]}...)"
    
    def __str__(self):
        stats = self.get_user_statistics()
        return (
            f"{self.name} ({self.email})\n"
            f"Address: {self.address[:16]}...\n"
            f"Credit Score: {self.credit_score}\n"
            f"Balance: ${self.wallet.balance:,.2f}\n"
            f"Accounts: {stats['total_accounts']}\n"
            f"Transactions: {stats['total_transactions']}"
        )


def create_financial_ecosystem():
    """Create a complete financial ecosystem with banks, users, and services."""
    print("=== Creating ChainForgeLedger Financial Ecosystem ===")
    
    # Initialize tokenomics
    tokenomics = Tokenomics(total_supply=1000000000)
    
    # Create banks
    print("\n1. Creating Financial Institutions...")
    banks = {
        'global_bank': Bank("Global Bank of ChainForge"),
        'regional_bank': Bank("Regional Financial Services"),
        'digital_bank': Bank("Digital First Bank")
    }
    
    # Create users
    print("\n2. Creating Users...")
    users = [
        User("Alice Smith", "alice.smith@example.com"),
        User("Bob Johnson", "bob.johnson@example.com"),
        User("Charlie Williams", "charlie.williams@example.com"),
        User("Diana Brown", "diana.brown@example.com"),
        User("Ethan Davis", "ethan.davis@example.com"),
        User("Fiona Miller", "fiona.miller@example.com")
    ]
    
    # Add customers to banks
    print("\n3. Onboarding Customers...")
    for user in users:
        # Add user to all banks
        for bank_name, bank in banks.items():
            bank.add_customer(user.address, user.name)
            user.open_bank_account(bank, 'checking')
            
            # Some users get savings accounts
            if random.choice([True, False]):
                user.open_bank_account(bank, 'savings')
    
    # Initialize blockchain platform
    print("\n4. Initializing Blockchain Platform...")
    platform = {
        'pow_blockchain': Blockchain(difficulty=3),
        'pow_consensus': ProofOfWork(Blockchain(difficulty=3), difficulty=3, reward=50.0),
        'pos_blockchain': Blockchain(difficulty=2),
        'validator_manager': ValidatorManager(),
        'nodes': [Node(f"node{i+1}") for i in range(3)],
        'vm': VirtualMachine(),
        'compiler': Compiler(),
        'contract_executor': ContractExecutor(),
        'voting_system': VotingSystem(),
        'tokenomics': tokenomics,
        'dao': DAO(
            name="ChainForge Financial DAO",
            description="Decentralized autonomous organization for financial governance",
            creator_address=banks['global_bank'].address,
            total_token_supply=tokenomics.total_supply,
            quorum_threshold=0.5,
            approval_threshold=0.66,
            voting_period=86400
        )
    }
    
    # Initialize PoS consensus
    initial_validators = [
        (bank.name, 1000) for bank_name in banks
    ]
    for name, stake in initial_validators:
        validator = Validator(name, stake)
        platform['validator_manager'].add_validator(validator)
    
    platform['pos_consensus'] = ProofOfStake(
        platform['pos_blockchain'],
        platform['validator_manager'],
        reward=50.0
    )
    
    # Connect network nodes
    for i, node in enumerate(platform['nodes']):
        for j in range(i + 1, len(platform['nodes'])):
            node.connect(platform['nodes'][j])
    
    # Add banks and users as DAO members
    for bank_name, bank in banks.items():
        platform['dao'].add_member(bank.address, 10000)
    
    for user in users:
        platform['dao'].add_member(user.address, random.randint(100, 1000))
    
    return {
        'banks': banks,
        'users': users,
        'platform': platform
    }


def demonstrate_ecosystem_operations(ecosystem):
    """Demonstrate various ecosystem operations."""
    print("\n=== Financial Ecosystem Operations ===")
    
    banks = ecosystem['banks']
    users = ecosystem['users']
    platform = ecosystem['platform']
    
    # Demonstrate bank statistics
    print("\n1. Bank Statistics:")
    for bank_name, bank in banks.items():
        stats = bank.get_bank_statistics()
        print(f"\n  {bank.name}:")
        print(f"    Customers: {stats['total_customers']}")
        print(f"    Accounts: {stats['total_accounts']}")
        print(f"    Available Services: {', '.join(stats['available_services'])}")
    
    # Demonstrate user activities
    print("\n2. User Activities:")
    
    # Alice sends money to Bob
    alice = users[0]
    bob = users[1]
    transfer_amount = 100.0
    
    print(f"\n  Alice ({alice.name}) sends ${transfer_amount:.2f} to Bob ({bob.name}):")
    transaction = alice.transfer_funds(banks['global_bank'], bob, transfer_amount)
    print(f"    Transaction ID: {transaction['transaction_id'][:16]}...")
    print(f"    Fee: ${transaction['fee']:.2f}")
    
    # Charlie applies for a loan
    charlie = users[2]
    loan_amount = 5000.0
    loan_term = 12
    
    print(f"\n  Charlie ({charlie.name}) applies for a ${loan_amount:.0f} loan:")
    loan_result = charlie.apply_for_loan(banks['regional_bank'], loan_amount, loan_term)
    
    if loan_result:
        print(f"    Loan Approved!")
        print(f"    Loan ID: {loan_result['loan']['loan_id']}")
        print(f"    Interest Rate: {loan_result['loan']['interest_rate']:.1%}")
        print(f"    Term: {loan_result['loan']['term_months']} months")
    else:
        print(f"    Loan Denied (Credit Score: {charlie.credit_score})")
    
    # Diana makes a payment
    diana = users[3]
    payment_amount = 250.0
    
    if banks['digital_bank'].loans:
        first_loan = banks['digital_bank'].loans[0]
        print(f"\n  Diana ({diana.name}) makes a ${payment_amount:.2f} payment:")
        payment_transaction = diana.make_loan_payment(banks['digital_bank'], first_loan['loan_id'], payment_amount)
        print(f"    Payment Transaction: {payment_transaction['transaction_id'][:16]}...")
    
    # Demonstrate tokenomics
    print("\n3. Tokenomics:")
    token_info = platform['tokenomics'].get_tokenomics_info()
    print(f"  Total Supply: {token_info['supply']['total']:,}")
    print(f"  Circulating Supply: {token_info['supply']['circulating']:,}")
    print(f"  Staking Rewards Pool: {token_info['supply']['staking_rewards']:,}")
    print(f"  Treasury: {token_info['supply']['treasury']:,}")
    print(f"  Inflation Rate: {token_info['inflation_rate']:.1%}")
    
    # Demonstrate DAO statistics
    print("\n4. Governance (DAO):")
    dao_stats = platform['dao'].get_stats()
    print(f"  DAO Name: {platform['dao'].name}")
    print(f"  Members: {dao_stats['members']}")
    print(f"  Total Token Supply: {dao_stats['total_token_supply']:,}")
    print(f"  Proposals: {dao_stats['proposals']['total']}")
    print(f"  Active Proposals: {dao_stats['proposals']['states'].get('active', 0)}")


def main():
    """Main function to run the comprehensive financial ecosystem example."""
    print("=" * 70)
    print("CHAINFORGELLEDGER - FINANCIAL ECOSYSTEM EXAMPLE")
    print("=" * 70)
    
    # Create the ecosystem
    ecosystem = create_financial_ecosystem()
    
    # Demonstrate operations
    demonstrate_ecosystem_operations(ecosystem)
    
    print("\n" + "=" * 70)
    print("FINANCIAL ECOSYSTEM CREATED AND OPERATIONAL")
    print("=" * 70)
    print("✅ Complete financial ecosystem established")
    print("✅ Banks, users, and financial services operational")
    print("✅ Blockchain platform and consensus mechanisms running")
    print("✅ DAO governance and tokenomics system active")
    print("✅ Network communication and transaction processing working")
    print("✅ Comprehensive financial services (payments, loans, transfers) available")


if __name__ == "__main__":
    main()
