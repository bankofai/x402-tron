"""PaymentPermit Facilitator 测试 - 演示验证和结算功能"""

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
# Use the address derived from TRON_PRIVATE_KEY as the buyer
# This is important: the buyer must be the one signing the permit
from tronpy.keys import PrivateKey
_pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY[2:] if TRON_PRIVATE_KEY.startswith("0x") else TRON_PRIVATE_KEY))
BUYER_ADDRESS = _pk.public_key.to_base58check_address()
# Use a valid test address (generated from test private key)
MERCHANT_ADDRESS = os.getenv("MERCHANT_ADDRESS", "TCNkawTmcQgYSU8nP8cHswT1QPjharxJr7")


async def run_facilitator_settle():
    """Facilitator 结算流程示例"""
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
        asset=TEST_USDT_ADDRESS,
        payTo=MERCHANT_ADDRESS,
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
    random_payment_id = "0x" + secrets.token_hex(16)
    # Use timestamp as nonce to ensure uniqueness
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


async def run_fee_quote():
    """费用报价功能示例"""
    signer = TronFacilitatorSigner.from_private_key(
        TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1]
    )
    mechanism = UptoTronFacilitatorMechanism(
        signer,
        fee_to=signer.get_address(),
        base_fee=0
    )

    requirements = PaymentRequirements(
        scheme="exact",
        network=TRON_NETWORK,
        amount="1000000",
        asset=TEST_USDT_ADDRESS,
        payTo=MERCHANT_ADDRESS,
    )

    return await mechanism.fee_quote(requirements)


async def main():
    if not TRON_PRIVATE_KEY:
        raise ValueError("TRON_PRIVATE_KEY not set in .env file")

    await run_fee_quote()
    await run_facilitator_settle()


if __name__ == "__main__":
    asyncio.run(main())
