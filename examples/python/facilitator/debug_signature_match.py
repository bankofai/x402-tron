"""Debug script to verify signature matches what contract expects"""

import os
import time
import secrets
from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_typed_data
import base58

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TEST_USDT_ADDRESS = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"
MERCHANT_ADDRESS = "TCNkawTmcQgYSU8nP8cHswT1QPjharxJr7"
PAYMENT_PERMIT_ADDRESS = "TQeYAZmGwYJTNcqKFjc5rfE2r1FfFVTpvF"

def tron_to_evm(tron_addr: str) -> str:
    """Convert TRON address to EVM format"""
    if tron_addr.startswith("0x"):
        return tron_addr
    try:
        decoded = base58.b58decode(tron_addr)
        address_bytes = decoded[1:21]
        return "0x" + address_bytes.hex()
    except:
        return tron_addr

def test_signature():
    """Test signature creation and recovery"""
    from tronpy.keys import PrivateKey
    
    # Get addresses
    pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
    buyer_tron = pk.public_key.to_base58check_address()
    buyer_evm = tron_to_evm(buyer_tron)
    
    print("=" * 70)
    print("Signature Match Test")
    print("=" * 70)
    print()
    print(f"Buyer (TRON): {buyer_tron}")
    print(f"Buyer (EVM): {buyer_evm}")
    print()
    
    # Create test permit matching actual call
    current_time = int(time.time())
    payment_id = "0x" + secrets.token_hex(16)
    nonce = current_time
    
    # Convert addresses to EVM format
    usdt_evm = tron_to_evm(TEST_USDT_ADDRESS)
    merchant_evm = tron_to_evm(MERCHANT_ADDRESS)
    permit_evm = tron_to_evm(PAYMENT_PERMIT_ADDRESS)
    zero_evm = "0x" + "00" * 20
    
    print(f"Test parameters:")
    print(f"  paymentId: {payment_id}")
    print(f"  nonce: {nonce}")
    print(f"  USDT (EVM): {usdt_evm}")
    print(f"  Merchant (EVM): {merchant_evm}")
    print(f"  PaymentPermit (EVM): {permit_evm}")
    print()
    
    # Create EIP-712 message
    domain = {
        "name": "PaymentPermit",
        "version": "1",
        "chainId": 3448148188,  # TRON Nile
        "verifyingContract": permit_evm,
    }
    
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "PermitMeta": [
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
        "PaymentPermit": [
            {"name": "meta", "type": "PermitMeta"},
            {"name": "buyer", "type": "address"},
            {"name": "caller", "type": "address"},
            {"name": "payment", "type": "Payment"},
            {"name": "fee", "type": "Fee"},
            {"name": "delivery", "type": "Delivery"},
        ],
    }
    
    message = {
        "meta": {
            "kind": 0,  # PAYMENT_ONLY
            "paymentId": payment_id,
            "nonce": nonce,
            "validAfter": 0,
            "validBefore": current_time + 3600,
        },
        "buyer": buyer_evm,
        "caller": zero_evm,
        "payment": {
            "payToken": usdt_evm,
            "maxPayAmount": 1000000,
            "payTo": merchant_evm,
        },
        "fee": {
            "feeTo": zero_evm,
            "feeAmount": 0,
        },
        "delivery": {
            "receiveToken": zero_evm,
            "miniReceiveAmount": 0,
            "tokenId": 0,
        },
    }
    
    print("-" * 70)
    print("Creating and verifying signature")
    print("-" * 70)
    
    typed_data = {
        "types": types,
        "primaryType": "PaymentPermit",
        "domain": domain,
        "message": message,
    }
    
    # Sign
    signable = encode_typed_data(full_message=typed_data)
    private_key_bytes = bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY)
    signed = Account.sign_message(signable, private_key_bytes)
    
    # Create signature
    r = signed.r.to_bytes(32, 'big')
    s = signed.s.to_bytes(32, 'big')
    v = signed.v
    signature = (r + s + v.to_bytes(1, 'big')).hex()
    
    print(f"✓ Signature created: {signature[:20]}...")
    print(f"  v: {v}")
    print()
    
    # Verify recovery
    recovered = Account.recover_message(signable, signature=bytes.fromhex(signature))
    matches = recovered.lower() == buyer_evm.lower()
    
    print(f"✓ Recovered address: {recovered}")
    print(f"✓ Expected address: {buyer_evm}")
    print(f"✓ Match: {matches}")
    print()
    
    if matches:
        print("=" * 70)
        print("SUCCESS: Signature verification works correctly!")
        print("=" * 70)
        print()
        print("The issue must be in the contract call encoding or parameters.")
    else:
        print("=" * 70)
        print("FAILURE: Signature recovery does not match!")
        print("=" * 70)

if __name__ == "__main__":
    test_signature()
