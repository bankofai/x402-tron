"""Debug script to test PaymentPermit contract state and interfaces"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from tronpy import Tron
from tronpy.keys import PrivateKey

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from x402.config import NetworkConfig

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "nile"
PAYMENT_PERMIT_ADDRESS = NetworkConfig.get_payment_permit_address("tron:nile")

def test_contract_state():
    """Test PaymentPermit contract state and interfaces"""
    
    # Initialize client
    client = Tron(network=TRON_NETWORK)
    
    # Get owner address from private key
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    owner_address = pk.public_key.to_base58check_address()
    
    print("=" * 70)
    print("PaymentPermit Contract State Test")
    print("=" * 70)
    print()
    
    print(f"Owner address: {owner_address}")
    print(f"PaymentPermit contract: {PAYMENT_PERMIT_ADDRESS}")
    print()
    
    # Get contract
    contract = client.get_contract(PAYMENT_PERMIT_ADDRESS)
    
    # Test 1: Check contract code
    print("-" * 70)
    print("Test 1: Contract Code")
    print("-" * 70)
    try:
        # Get contract info from blockchain
        contract_info = client.get_contract(PAYMENT_PERMIT_ADDRESS)
        print(f"✓ Contract exists and is accessible")
        print(f"  Contract address: {PAYMENT_PERMIT_ADDRESS}")
    except Exception as e:
        print(f"✗ Failed to get contract: {e}")
    print()
    
    # Test 2: Test nonceUsed with current owner
    print("-" * 70)
    print("Test 2: nonceUsed Interface")
    print("-" * 70)
    try:
        nonce = 1768288750
        result = contract.functions.nonceUsed(owner_address, nonce)
        print(f"✓ nonceUsed({owner_address}, {nonce}) = {result}")
    except Exception as e:
        print(f"✗ Failed to call nonceUsed: {e}")
    print()
    
    # Test 3: Check contract ABI
    print("-" * 70)
    print("Test 3: Contract ABI")
    print("-" * 70)
    try:
        if hasattr(contract, 'abi') and contract.abi:
            print(f"✓ Contract ABI available")
            print(f"  Number of functions: {len([x for x in contract.abi if x.get('type') == 'function'])}")
            
            # List all functions
            functions = [x for x in contract.abi if x.get('type') == 'function']
            print(f"\n  Available functions:")
            for func in functions:
                name = func.get('name', 'unknown')
                inputs = len(func.get('inputs', []))
                print(f"    - {name}({inputs} inputs)")
        else:
            print(f"✗ Contract ABI not available")
    except Exception as e:
        print(f"✗ Failed to check ABI: {e}")
    print()
    
    # Test 4: Test permitTransferFrom signature
    print("-" * 70)
    print("Test 4: permitTransferFrom Method Signature")
    print("-" * 70)
    try:
        if hasattr(contract, 'abi') and contract.abi:
            permit_func = None
            for func in contract.abi:
                if func.get('name') == 'permitTransferFrom':
                    permit_func = func
                    break
            
            if permit_func:
                print(f"✓ permitTransferFrom found in ABI")
                print(f"  Inputs ({len(permit_func.get('inputs', []))} total):")
                for i, inp in enumerate(permit_func.get('inputs', [])):
                    name = inp.get('name', f'param{i}')
                    type_ = inp.get('type', 'unknown')
                    print(f"    [{i}] {name}: {type_}")
                print(f"  Outputs: {len(permit_func.get('outputs', []))}")
            else:
                print(f"✗ permitTransferFrom not found in ABI")
        else:
            print(f"✗ Contract ABI not available")
    except Exception as e:
        print(f"✗ Failed to check permitTransferFrom: {e}")
    print()
    
    # Test 5: Get contract balance (if applicable)
    print("-" * 70)
    print("Test 5: Contract Account Info")
    print("-" * 70)
    try:
        account = client.get_account(PAYMENT_PERMIT_ADDRESS)
        balance = account.get('balance', 0)
        print(f"✓ Contract account info retrieved")
        print(f"  Balance: {balance} sun ({balance / 1e6} TRX)")
    except Exception as e:
        print(f"✗ Failed to get account info: {e}")
    print()
    
    print("=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_contract_state()
