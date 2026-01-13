"""Debug script to check token balance and allowance"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from tronpy import Tron

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from x402.config import NetworkConfig

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "nile"
TEST_USDT_ADDRESS = os.getenv("TEST_USDT_ADDRESS", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf")
PAYMENT_PERMIT_ADDRESS = NetworkConfig.get_payment_permit_address("tron:nile")

async def check_balance_and_allowance():
    """Check token balance and allowance"""
    from tronpy.keys import PrivateKey
    
    # Initialize client
    client = Tron(network=TRON_NETWORK)
    
    # Get owner address
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    owner_address = pk.public_key.to_base58check_address()
    
    print(f"Owner address: {owner_address}")
    print(f"Token address: {TEST_USDT_ADDRESS}")
    print(f"Spender (PaymentPermit): {PAYMENT_PERMIT_ADDRESS}")
    print()
    
    # Get token contract
    token_contract = client.get_contract(TEST_USDT_ADDRESS)
    
    # Check balance
    try:
        balance = token_contract.functions.balanceOf(owner_address)
        print(f"✓ Token balance: {balance}")
    except Exception as e:
        print(f"✗ Failed to get balance: {e}")
    
    # Check allowance
    try:
        allowance = token_contract.functions.allowance(owner_address, PAYMENT_PERMIT_ADDRESS)
        print(f"✓ Allowance: {allowance}")
    except Exception as e:
        print(f"✗ Failed to get allowance: {e}")
    
    # Check if balance >= amount needed
    amount_needed = 1000000
    if balance >= amount_needed:
        print(f"✓ Sufficient balance: {balance} >= {amount_needed}")
    else:
        print(f"✗ Insufficient balance: {balance} < {amount_needed}")
    
    # Check if allowance >= amount needed
    if allowance >= amount_needed:
        print(f"✓ Sufficient allowance: {allowance} >= {amount_needed}")
    else:
        print(f"✗ Insufficient allowance: {allowance} < {amount_needed}")

if __name__ == "__main__":
    asyncio.run(check_balance_and_allowance())
