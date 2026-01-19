"""
UptoEvmClientMechanism - "upto" 支付方案的 EVM 客户端机制
"""

from typing import Any, TYPE_CHECKING

from x402.abi import get_payment_permit_eip712_types
from x402.config import NetworkConfig
from x402.mechanisms.client.base import ClientMechanism
from x402.types import (
    PaymentPayload,
    PaymentPayloadData,
    PaymentPermit,
    PaymentRequirements,
    PermitMeta,
    Payment,
    Fee,
    Delivery,
    ResourceInfo,
    PAYMENT_ONLY,
)
from x402.utils import EVM_ZERO_ADDRESS, convert_permit_to_eip712_message

if TYPE_CHECKING:
    from x402.signers.client import ClientSigner


class UptoEvmClientMechanism(ClientMechanism):
    """"upto" 支付方案的 EVM 客户端机制"""

    def __init__(self, signer: "ClientSigner") -> None:
        self._signer = signer

    def scheme(self) -> str:
        return "exact"

    async def create_payment_payload(
        self,
        requirements: PaymentRequirements,
        resource: str,
        extensions: dict[str, Any] | None = None,
    ) -> PaymentPayload:
        """使用 EIP-712 签名创建支付载荷"""
        context = extensions.get("paymentPermitContext") if extensions else None
        if context is None:
            raise ValueError("paymentPermitContext is required")

        permit = self._build_permit(requirements, context)
        
        await self._ensure_allowance(permit, requirements.network)
        
        signature = await self._sign_permit(permit, requirements.network)

        return PaymentPayload(
            x402Version=2,
            resource=ResourceInfo(url=resource),
            accepted=requirements,
            payload=PaymentPayloadData(
                signature=signature,
                paymentPermit=permit,
            ),
            extensions={},
        )

    def _build_permit(
        self,
        requirements: PaymentRequirements,
        context: dict[str, Any],
    ) -> PaymentPermit:
        """Build PaymentPermit from requirements and context"""
        buyer_address = self._signer.get_address()
        meta = context.get("meta", {})
        delivery = context.get("delivery", {})

        fee_to = EVM_ZERO_ADDRESS
        fee_amount = "0"
        if requirements.extra and requirements.extra.fee:
            fee_to = requirements.extra.fee.fee_to
            fee_amount = requirements.extra.fee.fee_amount

        caller = context.get("caller") or EVM_ZERO_ADDRESS

        return PaymentPermit(
            meta=PermitMeta(
                kind=meta.get("kind", PAYMENT_ONLY),
                paymentId=meta.get("paymentId", ""),
                nonce=str(meta.get("nonce", "0")),
                validAfter=meta.get("validAfter", 0),
                validBefore=meta.get("validBefore", 0),
            ),
            buyer=buyer_address,
            caller=caller,
            payment=Payment(
                payToken=requirements.asset,
                maxPayAmount=requirements.amount,
                payTo=requirements.pay_to,
            ),
            fee=Fee(
                feeTo=fee_to,
                feeAmount=fee_amount,
            ),
            delivery=Delivery(
                receiveToken=delivery.get("receiveToken", EVM_ZERO_ADDRESS),
                miniReceiveAmount=str(delivery.get("miniReceiveAmount", "0")),
                tokenId=str(delivery.get("tokenId", "0")),
            ),
        )

    async def _ensure_allowance(self, permit: PaymentPermit, network: str) -> None:
        """Ensure token allowance for payment + fee"""
        total_amount = int(permit.payment.max_pay_amount) + int(permit.fee.fee_amount)
        await self._signer.ensure_allowance(
            permit.payment.pay_token,
            total_amount,
            network,
        )

    async def _sign_permit(self, permit: PaymentPermit, network: str) -> str:
        """Sign permit with EIP-712"""
        permit_address = NetworkConfig.get_payment_permit_address(network)
        chain_id = NetworkConfig.get_chain_id(network)
        
        message = convert_permit_to_eip712_message(permit)
        
        return await self._signer.sign_typed_data(
            domain={
                "name": "PaymentPermit",
                "chainId": chain_id,
                "verifyingContract": permit_address,
            },
            types=get_payment_permit_eip712_types(),
            message=message,
        )
