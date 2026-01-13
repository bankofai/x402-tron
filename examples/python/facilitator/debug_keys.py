"""Debug script to verify private key and address correspondence"""

import os
from pathlib import Path
from dotenv import load_dotenv
from tronpy.keys import PrivateKey

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
BUYER_ADDRESS = os.getenv("BUYER_ADDRESS", "TLBaRhANhwgZyUk6Z1ynCn1Ld7BRH1jBjZ")

def check_keys():
    """Check if private key matches the buyer address"""
    
    # Get address from private key
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    derived_address = pk.public_key.to_base58check_address()
    
    print(f"Private key: {TRON_PRIVATE_KEY[:20]}...")
    print(f"Derived address: {derived_address}")
    print(f"Buyer address (from env): {BUYER_ADDRESS}")
    print()
    
    if derived_address.lower() == BUYER_ADDRESS.lower():
        print("✓ Private key matches buyer address")
    else:
        print("✗ Private key DOES NOT match buyer address")
        print()
        print("This is the problem! The private key should derive to the buyer address.")
        print("The facilitator is using a different private key than the buyer.")

if __name__ == "__main__":
    check_keys()
