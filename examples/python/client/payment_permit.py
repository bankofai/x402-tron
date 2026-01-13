"""PaymentPermit 客户端授权测试"""

import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from x402.logging_config import setup_logging
from x402.mechanisms.client import UptoTronClientMechanism
from x402.signers.client import TronClientSigner
from x402.types import PaymentRequirements, PaymentRequirementsExtra, FeeInfo

setup_logging()
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
TRON_NETWORK = "tron:nile"
# Use valid TRON addresses from Nile testnet
TEST_USDT_ADDRESS = os.getenv("TEST_USDT_ADDRESS", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf")
MERCHANT_ADDRESS = os.getenv("MERCHANT_ADDRESS", "TLBaRhANhwgZyUk6Z1ynCn1Ld7BRH1jBjZ")
FACILITATOR_ADDRESS = os.getenv("FACILITATOR_ADDRESS", "TQn9Y2khEsNJey1pqjPPsGezRQqKS2eqA7")


async def run_client_authorization():
    """客户端授权流程示例"""
    # 创建客户端
    # 需要传入 network 以便在需要时（如授权额度不足）自动初始化 Tron 客户端执行批准交易
    signer = TronClientSigner.from_private_key(TRON_PRIVATE_KEY, network=TRON_NETWORK.split(":")[-1])
    mechanism = UptoTronClientMechanism(signer)

    # 构造支付要求
    requirements = PaymentRequirements(
        scheme="exact",
        network=TRON_NETWORK,
        amount="1000000",
        asset=TEST_USDT_ADDRESS,
        payTo=MERCHANT_ADDRESS,
    )

    # 构造支付许可上下文
    permit_context = {
        "paymentPermitContext": {
            "meta": {
                "kind": "PAYMENT_ONLY",
                "paymentId": "0x" + "12" * 16,
                "nonce": "1",
                "validAfter": 0,
                "validBefore": int(time.time()) + 3600,
            },
            "delivery": {
                "receiveToken": "T" + "0" * 33,
                "miniReceiveAmount": "0",
                "tokenId": "0",
            },
        }
    }

    # 创建支付载荷
    payload = await mechanism.create_payment_payload(
        requirements,
        "https://api.example.com/resource",
        extensions=permit_context,
    )
    
    return payload


async def main():
    if not TRON_PRIVATE_KEY:
        print("\n❌ Error: TRON_PRIVATE_KEY not set in .env file")
        print("\nPlease add your TRON private key to /Users/wdk/tron/x402/.env:")
        print("  TRON_PRIVATE_KEY=your_actual_private_key_here\n")
        return
    
    await run_client_authorization()
    print("✅ Payment authorization completed successfully\n")


if __name__ == "__main__":
    asyncio.run(main())
