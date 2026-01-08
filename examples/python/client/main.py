import asyncio
import os
from dotenv import load_dotenv
import httpx

from x402.clients import X402Client, X402HttpClient
from x402.mechanisms.client import UptoTronClientMechanism
from x402.signers.client import TronClientSigner

load_dotenv()

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY", "")
RESOURCE_URL = os.getenv("RESOURCE_SERVER_URL", "http://localhost:4021") + os.getenv("ENDPOINT_PATH", "/protected")

async def main():
    # 1. 设置客户端
    signer = TronClientSigner.from_private_key(TRON_PRIVATE_KEY)
    x402_client = X402Client().register("tron:*", UptoTronClientMechanism(signer))
    
    async with httpx.AsyncClient() as http_client:
        client = X402HttpClient(http_client, x402_client)
        
        print(f"Requesting: {RESOURCE_URL}")
        try:
            # 2. 发起请求（自动处理 402 支付）
            response = await client.get(RESOURCE_URL)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
