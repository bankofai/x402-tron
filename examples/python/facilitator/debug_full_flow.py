"""Debug script to trace the full payment flow with detailed logging"""

import asyncio
import os
import time
import secrets
from pathlib import Path
from dotenv import load_dotenv

from x402.logging_config import setup_logging
from x402.mechanisms.client import UptoTronClientMechanism
from x402.mechanisms.facilitator import UptoTronFacilitatorMechanism
from x402.signers.client import TronClientSigner
from x402.signers.facilitator import TronFacilitatorSigner
from x402.types import PaymentRequirements

setup_logging()
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "tron:nile"
TEST_USDT_ADDRESS = os.getenv("TEST_USDT_ADDRESS", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf")
MERCHANT_ADDRESS = os.getenv("MERCHANT_ADDRESS", "TCNkawTmcQgYSU8nP8cHswT1QPjharxJr7")

async def main():
    """Run full payment flow with detailed logging"""
    
    # Setup
    facilitator_signer = TronFacilitatorSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    facilitator_address = facilitator_signer.get_address()
    facilitator_mechanism = UptoTronFacilitatorMechanism(
        facilitator_signer,
        fee_to=facilitator_address,
        base_fee=0
    )

    requirements = PaymentRequirements(
        scheme="exact",
        network=TRON_NETWORK,
        amount="1000000",
        asset=TEST_USDT_ADDRESS,
        payTo=MERCHANT_ADDRESS,
    )

    client_signer = TronClientSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    client_mechanism = UptoTronClientMechanism(client_signer)

    current_time = int(time.time())
    random_payment_id = "0x" + secrets.token_hex(16)
    nonce = str(current_time)
    
    permit_context = {
        "paymentPermitContext": {
            "meta": {
                "kind": "PAYMENT_ONLY",
                "paymentId": random_payment_id,
                "nonce": nonce,
                "validAfter": 0,
                "validBefore": current_time + 3600,
            },
            "delivery": {
                "receiveToken": "T" + "0" * 33,
                "miniReceiveAmount": "0",
                "tokenId": "0",
            },
        }
    }
    
    print("=" * 70)
    print("Full Payment Flow Debug")
    print("=" * 70)
    print(f"Payment ID: {random_payment_id}")
    print(f"Nonce: {nonce}")
    print(f"Buyer: {client_signer.get_address()}")
    print(f"Merchant: {MERCHANT_ADDRESS}")
    print(f"Amount: 1000000")
    print("=" * 70)
    print()

    # Create payload
    print("Step 1: Creating payment payload...")
    payload = await client_mechanism.create_payment_payload(
        requirements,
        "https://api.example.com/resource",
        extensions=permit_context,
    )
    print(f"✓ Payload created")
    print(f"  Signature: {payload.payload.signature[:20]}...")
    print(f"  Buyer: {payload.payload.payment_permit.buyer}")
    print(f"  Caller: {payload.payload.payment_permit.caller}")
    print()

    # Verify
    print("Step 2: Verifying payment...")
    verify_result = await facilitator_mechanism.verify(payload, requirements)
    print(f"✓ Verification result: {verify_result.is_valid}")
    if not verify_result.is_valid:
        print(f"  Reason: {verify_result.invalid_reason}")
        return
    print()

    # Settle
    print("Step 3: Settling payment...")
    print("  This will call permitTransferFrom on the contract")
    print("  Watch for any errors in the transaction...")
    print()
    
    settle_result = await facilitator_mechanism.settle(payload, requirements)
    
    print()
    print("=" * 70)
    print("Settlement Result")
    print("=" * 70)
    print(f"Success: {settle_result.success}")
    if settle_result.success:
        print(f"Transaction: {settle_result.transaction}")
    else:
        print(f"Error: {settle_result.error_reason}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
