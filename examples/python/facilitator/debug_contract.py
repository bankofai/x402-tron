"""PaymentPermit Facilitator Test - Demonstrates verification and settlement functionality"""

import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from x402.logging_config import setup_logging
from x402.mechanisms.client import UptoTronClientMechanism
from x402.mechanisms.facilitator import UptoTronFacilitatorMechanism
from x402.signers.client import TronClientSigner
from x402.signers.facilitator import TronFacilitatorSigner
from x402.types import PaymentRequirements, PAYMENT_ONLY, PAYMENT_AND_DELIVERY

setup_logging()
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "tron:nile"
USDT_TOKEN_ADDRESS = os.getenv("USDT_TOKEN_ADDRESS", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf")
# Use the address derived from TRON_PRIVATE_KEY as the buyer
# This is important: the buyer must be the one signing the permit
from tronpy.keys import PrivateKey
_pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
BUYER_ADDRESS = _pk.public_key.to_base58check_address()
# Merchant contract address for receiving payments
MERCHANT_CONTRACT_ADDRESS = os.getenv("MERCHANT_CONTRACT_ADDRESS")


async def run_facilitator_settle():
    """Facilitator settlement flow example"""
    facilitator_signer = TronFacilitatorSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    facilitator_address = facilitator_signer.get_address()
    facilitator_mechanism = UptoTronFacilitatorMechanism(
        facilitator_signer,
        fee_to=facilitator_address,
        base_fee=0
    )

    # Create requirements with facilitator fee info so caller is set correctly
    from x402.types import FeeInfo, PaymentRequirementsExtra
    requirements = PaymentRequirements(
        scheme="exact",
        network=TRON_NETWORK,
        amount="1000000",
        asset=USDT_TOKEN_ADDRESS,
        payTo=MERCHANT_CONTRACT_ADDRESS,
        extra=PaymentRequirementsExtra(
            fee=FeeInfo(
                feeTo=facilitator_address,
                feeAmount="0"
            )
        )
    )

    client_signer = TronClientSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    client_mechanism = UptoTronClientMechanism(client_signer)

    current_time = int(time.time())
    # Generate random paymentId to avoid nonce conflicts
    from x402.utils import generate_payment_id
    random_payment_id = generate_payment_id()
    # Use timestamp as nonce to ensure uniqueness
    nonce = str(current_time)
    
    # TRON uses milliseconds for block.timestamp, so multiply by 1000
    current_time_ms = current_time * 1000
    
    permit_context = {
        "paymentPermitContext": {
            "meta": {
                "kind": PAYMENT_ONLY,
                "paymentId": random_payment_id,
                "nonce": nonce,
                "validAfter": 0,
                "validBefore": current_time_ms + 3600000,  # +1 hour in milliseconds
            },
            "delivery": {
                "receiveToken": "T" + "0" * 33,
                "miniReceiveAmount": "0",
                "tokenId": "0",
            },
        }
    }
    
    print(f"Using paymentId: {random_payment_id}, nonce: {nonce}")

    payload = await client_mechanism.create_payment_payload(
        requirements,
        "https://api.example.com/resource",
        extensions=permit_context,
    )

    verify_result = await facilitator_mechanism.verify(payload, requirements)
    if not verify_result.is_valid:
        return verify_result

    settle_result = await facilitator_mechanism.settle(payload, requirements)
    return settle_result


async def run_facilitator_settle_with_delivery():
    """Facilitator settlement flow example - PAYMENT_AND_DELIVERY scenario"""
    facilitator_signer = TronFacilitatorSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    facilitator_address = facilitator_signer.get_address()
    facilitator_mechanism = UptoTronFacilitatorMechanism(
        facilitator_signer,
        fee_to=facilitator_address,
        base_fee=0
    )

    # Create requirements with facilitator fee info so caller is set correctly
    from x402.types import FeeInfo, PaymentRequirementsExtra
    requirements = PaymentRequirements(
        scheme="exact",
        network=TRON_NETWORK,
        amount="1000000",
        asset=USDT_TOKEN_ADDRESS,
        payTo=MERCHANT_CONTRACT_ADDRESS,
        extra=PaymentRequirementsExtra(
            fee=FeeInfo(
                feeTo=facilitator_address,
                feeAmount="0"
            )
        )
    )

    client_signer = TronClientSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    client_mechanism = UptoTronClientMechanism(client_signer)

    current_time = int(time.time())
    # Generate random paymentId to avoid nonce conflicts
    from x402.utils import generate_payment_id
    random_payment_id = generate_payment_id()
    # Use timestamp as nonce to ensure uniqueness
    nonce = str(current_time)
    
    # TRON uses milliseconds for block.timestamp, so multiply by 1000
    current_time_ms = current_time * 1000
    
    # PAYMENT_AND_DELIVERY scenario: need to specify actual receive token and minimum receive amount
    # caller set to zero address, allows any address to call (including Merchant contract)
    permit_context = {
        "paymentPermitContext": {
            "meta": {
                "kind": PAYMENT_AND_DELIVERY,
                "paymentId": random_payment_id,
                "nonce": nonce,
                "validAfter": 0,
                "validBefore": current_time_ms + 3600000,  # +1 hour in milliseconds
            },
            "caller": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",  # TRON zero address, allows any address to call
            "delivery": {
                "receiveToken": USDT_TOKEN_ADDRESS,  # Actual receive token address
                "miniReceiveAmount": "500000",  # Minimum receive amount (0.5 USDT)
                "tokenId": "0",
            },
        }
    }
    
    print(f"[PAYMENT_AND_DELIVERY] Using paymentId: {random_payment_id}, nonce: {nonce}")
    print(f"[PAYMENT_AND_DELIVERY] Setting caller to TRON zero address: T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb")
    print(f"[PAYMENT_AND_DELIVERY] Expecting to receive at least 0.5 USDT")

    payload = await client_mechanism.create_payment_payload(
        requirements,
        "https://api.example.com/resource",
        extensions=permit_context,
    )

    verify_result = await facilitator_mechanism.verify(payload, requirements)
    if not verify_result.is_valid:
        print(f"[PAYMENT_AND_DELIVERY] Verification failed: {verify_result.invalid_reason}")
        return verify_result

    print("[PAYMENT_AND_DELIVERY] Verification passed, proceeding to settle...")
    settle_result = await facilitator_mechanism.settle(payload, requirements)
    return settle_result

async def main():
    if not TRON_PRIVATE_KEY:
        raise ValueError("TRON_PRIVATE_KEY not set in .env file")

    # Select test scenario to run
    await run_facilitator_settle()  # PAYMENT_ONLY scenario
    # await run_facilitator_settle_with_delivery()  # PAYMENT_AND_DELIVERY scenario


if __name__ == "__main__":
    asyncio.run(main())
