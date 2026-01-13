"""Debug script to verify EIP-712 signature recovery matches contract expectations"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_typed_data
import base58

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")

def tron_to_evm(tron_addr: str) -> str:
    """Convert TRON address to EVM format"""
    try:
        decoded = base58.b58decode(tron_addr)
        address_bytes = decoded[1:21]
        return "0x" + address_bytes.hex()
    except:
        return tron_addr

def test_signature_recovery():
    """Test EIP-712 signature recovery"""
    
    from tronpy.keys import PrivateKey
    
    # Get address from private key
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    owner_tron = pk.public_key.to_base58check_address()
    owner_evm = tron_to_evm(owner_tron)
    
    print("=" * 70)
    print("EIP-712 Signature Recovery Test")
    print("=" * 70)
    print()
    
    print(f"Owner (TRON): {owner_tron}")
    print(f"Owner (EVM): {owner_evm}")
    print()
    
    # Create a test EIP-712 message similar to PaymentPermit
    domain = {
        "name": "PaymentPermit",
        "version": "1",
        "chainId": 3448148188,  # TRON Nile
        "verifyingContract": "0x" + "02ea7c9bb4ebcfd58058baca86b6f663356a63ec",  # PaymentPermit contract
    }
    
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "PaymentPermit": [
            {"name": "meta", "type": "Meta"},
            {"name": "buyer", "type": "address"},
            {"name": "caller", "type": "address"},
            {"name": "payment", "type": "Payment"},
            {"name": "fee", "type": "Fee"},
            {"name": "delivery", "type": "Delivery"},
        ],
        "Meta": [
            {"name": "kind", "type": "uint8"},
            {"name": "paymentId", "type": "bytes16"},
            {"name": "nonce", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
        ],
        "Payment": [
            {"name": "payToken", "type": "address"},
            {"name": "maxPayAmount", "type": "uint256"},
            {"name": "payTo", "type": "address"},
        ],
        "Fee": [
            {"name": "feeTo", "type": "address"},
            {"name": "feeAmount", "type": "uint256"},
        ],
        "Delivery": [
            {"name": "receiveToken", "type": "address"},
            {"name": "miniReceiveAmount", "type": "uint256"},
            {"name": "tokenId", "type": "uint256"},
        ],
    }
    
    message = {
        "meta": {
            "kind": 0,
            "paymentId": "0x" + "12" * 16,
            "nonce": 1,
            "validAfter": 0,
            "validBefore": 9999999999,
        },
        "buyer": owner_evm,
        "caller": "0x" + "00" * 20,
        "payment": {
            "payToken": tron_to_evm("TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"),
            "maxPayAmount": 1000000,
            "payTo": tron_to_evm("TCNkawTmcQgYSU8nP8cHswT1QPjharxJr7"),
        },
        "fee": {
            "feeTo": "0x" + "00" * 20,
            "feeAmount": 0,
        },
        "delivery": {
            "receiveToken": "0x" + "00" * 20,
            "miniReceiveAmount": 0,
            "tokenId": 0,
        },
    }
    
    print("-" * 70)
    print("Creating EIP-712 Signature")
    print("-" * 70)
    
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
    
    print(f"✓ Signature created")
    print(f"  v: {signed.v}")
    print(f"  r: {signed.r.to_bytes(32, 'big').hex()}")
    print(f"  s: {signed.s.to_bytes(32, 'big').hex()}")
    print()
    
    # Test recovery
    print("-" * 70)
    print("Testing Signature Recovery")
    print("-" * 70)
    
    # Format 1: r + s + v (standard)
    r = signed.r.to_bytes(32, 'big')
    s = signed.s.to_bytes(32, 'big')
    v = signed.v
    
    sig_format1 = (r + s + v.to_bytes(1, 'big')).hex()
    try:
        recovered = Account.recover_message(signable, signature=bytes.fromhex(sig_format1))
        matches = recovered.lower() == owner_evm.lower()
        print(f"✓ Format 1 (r+s+v, v=27/28): {recovered}")
        print(f"  Matches owner? {matches}")
    except Exception as e:
        print(f"✗ Format 1 failed: {e}")
    
    print()
    
    # Format 2: r + s + (v-27) (0-indexed)
    v_indexed = v - 27
    sig_format2 = (r + s + v_indexed.to_bytes(1, 'big')).hex()
    try:
        recovered = Account.recover_message(signable, signature=bytes.fromhex(sig_format2))
        matches = recovered.lower() == owner_evm.lower()
        print(f"✓ Format 2 (r+s+v, v=0/1): {recovered}")
        print(f"  Matches owner? {matches}")
    except Exception as e:
        print(f"✗ Format 2 failed: {e}")
    
    print()
    print("=" * 70)
    print("Signature format verification complete")
    print("=" * 70)

if __name__ == "__main__":
    test_signature_recovery()
