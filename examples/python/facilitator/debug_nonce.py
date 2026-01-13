"""Debug script to test PaymentPermit contract nonceUsed interface"""

import os
from pathlib import Path
from dotenv import load_dotenv
from tronpy import Tron
from tronpy.keys import PrivateKey

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from x402.config import NetworkConfig

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "nile"
PAYMENT_PERMIT_ADDRESS = NetworkConfig.get_payment_permit_address("tron:nile")

def test_nonce_used():
    """Test the nonceUsed interface of PaymentPermit contract"""
    
    # Initialize client
    client = Tron(network=TRON_NETWORK)
    
    # Get owner address from private key
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    owner_address = pk.public_key.to_base58check_address()
    
    print(f"Owner address: {owner_address}")
    print(f"PaymentPermit contract: {PAYMENT_PERMIT_ADDRESS}")
    print()
    
    # Get contract
    contract = client.get_contract(PAYMENT_PERMIT_ADDRESS)
    
    # Test different nonce values
    test_nonces = [0, 1, 100, 1768288750, 9999999999]
    
    print("Testing nonceUsed interface:")
    print("-" * 60)
    
    for nonce in test_nonces:
        try:
            result = contract.functions.nonceUsed(owner_address, nonce)
            print(f"Nonce {nonce}: {result}")
        except Exception as e:
            print(f"Nonce {nonce}: ERROR - {e}")
    
    print()
    print("=" * 60)
    print("Test completed successfully!")

if __name__ == "__main__":
    test_nonce_used()
