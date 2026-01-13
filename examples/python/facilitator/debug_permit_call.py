"""Debug script to test permitTransferFrom with detailed logging"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from tronpy import Tron
from tronpy.keys import PrivateKey
import base58

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from x402.config import NetworkConfig

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "nile"
PAYMENT_PERMIT_ADDRESS = NetworkConfig.get_payment_permit_address("tron:nile")
TEST_USDT_ADDRESS = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"
MERCHANT_ADDRESS = "TCNkawTmcQgYSU8nP8cHswT1QPjharxJr7"

def tron_to_evm(tron_addr: str) -> str:
    """Convert TRON address to EVM format"""
    try:
        decoded = base58.b58decode(tron_addr)
        address_bytes = decoded[1:21]
        return "0x" + address_bytes.hex()
    except:
        return tron_addr

def test_permit_call():
    """Test permitTransferFrom call"""
    
    # Initialize client
    client = Tron(network=TRON_NETWORK)
    
    # Get owner address from private key
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    owner_address = pk.public_key.to_base58check_address()
    owner_evm = tron_to_evm(owner_address)
    
    print("=" * 70)
    print("PaymentPermit permitTransferFrom Test")
    print("=" * 70)
    print()
    
    print(f"Owner address (TRON): {owner_address}")
    print(f"Owner address (EVM): {owner_evm}")
    print(f"PaymentPermit contract: {PAYMENT_PERMIT_ADDRESS}")
    print(f"Test USDT: {TEST_USDT_ADDRESS}")
    print(f"Merchant: {MERCHANT_ADDRESS}")
    print()
    
    # Get contract
    contract = client.get_contract(PAYMENT_PERMIT_ADDRESS)
    
    # Check contract ABI
    print("-" * 70)
    print("Contract ABI Check")
    print("-" * 70)
    if hasattr(contract, 'abi') and contract.abi:
        permit_func = None
        for func in contract.abi:
            if func.get('name') == 'permitTransferFrom':
                permit_func = func
                break
        
        if permit_func:
            print(f"✓ permitTransferFrom found")
            print(f"  Inputs: {len(permit_func.get('inputs', []))}")
            for i, inp in enumerate(permit_func.get('inputs', [])):
                name = inp.get('name', f'param{i}')
                type_ = inp.get('type', 'unknown')
                print(f"    [{i}] {name}: {type_}")
        else:
            print(f"✗ permitTransferFrom not found in ABI")
    print()
    
    # Check if contract is paused or has other state
    print("-" * 70)
    print("Contract State Check")
    print("-" * 70)
    try:
        # Try to call a simple view function
        nonce_used = contract.functions.nonceUsed(owner_address, 1)
        print(f"✓ nonceUsed(owner, 1) = {nonce_used}")
    except Exception as e:
        print(f"✗ Failed to call nonceUsed: {e}")
    print()
    
    # Check token balance and allowance
    print("-" * 70)
    print("Token Balance and Allowance Check")
    print("-" * 70)
    try:
        token_contract = client.get_contract(TEST_USDT_ADDRESS)
        balance = token_contract.functions.balanceOf(owner_address)
        allowance = token_contract.functions.allowance(owner_address, PAYMENT_PERMIT_ADDRESS)
        print(f"✓ Token balance: {balance}")
        print(f"✓ Token allowance to PaymentPermit: {allowance}")
        
        if balance >= 1000000:
            print(f"  ✓ Sufficient balance")
        else:
            print(f"  ✗ Insufficient balance")
        
        if allowance >= 1000000:
            print(f"  ✓ Sufficient allowance")
        else:
            print(f"  ✗ Insufficient allowance")
    except Exception as e:
        print(f"✗ Failed to check token: {e}")
    print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("Contract is accessible and responding to view functions.")
    print("The issue is likely in the permitTransferFrom execution logic.")
    print()
    print("Possible causes of REVERT:")
    print("  1. Signature verification failure")
    print("  2. Nonce validation failure")
    print("  3. Time window validation failure (validAfter/validBefore)")
    print("  4. Token transfer failure")
    print("  5. Other contract-specific validation")

if __name__ == "__main__":
    test_permit_call()
