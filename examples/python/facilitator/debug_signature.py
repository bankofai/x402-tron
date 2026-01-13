"""Debug script to verify EIP-712 signature format"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_typed_data

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
BUYER_ADDRESS = os.getenv("BUYER_ADDRESS", "TLBaRhANhwgZyUk6Z1ynCn1Ld7BRH1jBjZ")

def test_signature_format():
    """Test EIP-712 signature format"""
    
    # Convert TRON address to EVM format
    from tronpy.keys import to_base58check_address
    import base58
    
    def tron_to_evm(tron_addr: str) -> str:
        """Convert TRON address to EVM format"""
        try:
            decoded = base58.b58decode(tron_addr)
            address_bytes = decoded[1:21]
            return "0x" + address_bytes.hex()
        except:
            return tron_addr
    
    buyer_evm = tron_to_evm(BUYER_ADDRESS)
    print(f"Buyer TRON: {BUYER_ADDRESS}")
    print(f"Buyer EVM: {buyer_evm}")
    print()
    
    # Create test EIP-712 message
    domain = {
        "name": "PaymentPermit",
        "version": "1",
        "chainId": 3448148188,  # TRON Nile
        "verifyingContract": "0x" + "11" * 20,
    }
    
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "PaymentPermit": [
            {"name": "test", "type": "uint256"},
        ],
    }
    
    message = {
        "test": 123,
    }
    
    typed_data = {
        "types": types,
        "primaryType": "PaymentPermit",
        "domain": domain,
        "message": message,
    }
    
    # Sign the message
    signable = encode_typed_data(full_message=typed_data)
    private_key_bytes = bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY)
    signed = Account.sign_message(signable, private_key_bytes)
    
    print("Signature components:")
    print(f"  r: {signed.r.to_bytes(32, 'big').hex()}")
    print(f"  s: {signed.s.to_bytes(32, 'big').hex()}")
    print(f"  v: {signed.v} (0x{signed.v:02x})")
    print()
    
    # Format as different signature formats
    r = signed.r.to_bytes(32, 'big')
    s = signed.s.to_bytes(32, 'big')
    v = signed.v
    
    # Format 1: r + s + v (standard Ethereum)
    sig_format1 = (r + s + v.to_bytes(1, 'big')).hex()
    print(f"Format 1 (r+s+v, v=27/28): 0x{sig_format1}")
    
    # Format 2: r + s + (v-27) (0-indexed v)
    v_indexed = v - 27
    sig_format2 = (r + s + v_indexed.to_bytes(1, 'big')).hex()
    print(f"Format 2 (r+s+v, v=0/1): 0x{sig_format2}")
    
    # Format 3: v + r + s (some contracts use this)
    sig_format3 = (v.to_bytes(1, 'big') + r + s).hex()
    print(f"Format 3 (v+r+s, v=27/28): 0x{sig_format3}")
    
    print()
    
    # Test recovery
    print("Testing signature recovery:")
    
    # Try to recover with format 1
    try:
        recovered = Account.recover_message(signable, signature=bytes.fromhex(sig_format1))
        print(f"  Format 1 recovered: {recovered}")
        print(f"  Matches buyer? {recovered.lower() == buyer_evm.lower()}")
    except Exception as e:
        print(f"  Format 1 failed: {e}")
    
    # Try to recover with format 2
    try:
        recovered = Account.recover_message(signable, signature=bytes.fromhex(sig_format2))
        print(f"  Format 2 recovered: {recovered}")
        print(f"  Matches buyer? {recovered.lower() == buyer_evm.lower()}")
    except Exception as e:
        print(f"  Format 2 failed: {e}")
    
    print()
    print("Full signature object:")
    print(f"  signature: {signed.signature.hex()}")
    print(f"  messageHash: {signed.messageHash.hex()}")

if __name__ == "__main__":
    test_signature_format()
