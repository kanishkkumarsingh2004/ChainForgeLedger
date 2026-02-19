"""
ChainForgeLedger Tokenomics Module

Token standards and supply management implementation:
- KK-20: Fungible token standard (similar to ERC-20)
- KK-721: Non-fungible token standard (similar to ERC-721)
- Token factory for token creation and management
- Supply control and distribution system
"""

from chainforgeledger.tokenomics.standards import KK20Token, KK721Token, TokenFactory
from chainforgeledger.tokenomics.supply import Tokenomics

__all__ = ["Tokenomics", "KK20Token", "KK721Token", "TokenFactory"]
