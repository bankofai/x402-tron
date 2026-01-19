"""
UptoEvmFacilitatorMechanism - "upto" 支付方案的 EVM facilitator 机制
"""

import time
from typing import Any, TYPE_CHECKING

from x402.abi import PAYMENT_PERMIT_ABI, MERCHANT_ABI, get_abi_json, get_payment_permit_eip712_types
from x402.config import NetworkConfig
from x402.mechanisms.facilitator.base import FacilitatorMechanism
from x402.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
    FeeQuoteResponse,
    FeeInfo,
    PAYMENT_AND_DELIVERY,
)
from x402.utils import convert_permit_to_eip712_message

if TYPE_CHECKING:
    from x402.signers.facilitator import FacilitatorSigner


class UptoEvmFacilitatorMechanism(FacilitatorMechanism):
    """"upto" 支付方案的 EVM facilitator 机制"""

    def __init__(
        self,
        signer: "FacilitatorSigner",
        fee_to: str | None = None,
        base_fee: int = 1000000,
    ) -> None:
        self._signer = signer
        self._fee_to = fee_to or signer.get_address()
        self._base_fee = base_fee

    def scheme(self) -> str:
        return "exact"

    async def fee_quote(
        self,
        accept: PaymentRequirements,
        context: dict[str, Any] | None = None,
    ) -> FeeQuoteResponse:
        """基于 gas 估算计算费用报价"""
        return FeeQuoteResponse(
            fee=FeeInfo(
                feeTo=self._fee_to,
                feeAmount=str(self._base_fee),
            ),
            pricing="per_accept",
            network=accept.network,
            expiresAt=int(time.time()) + 300,
        )

    async def verify(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """验证支付签名"""
        permit = payload.payload.payment_permit
        
        # Validate permit against requirements
        validation_error = self._validate_permit(permit, requirements)
        if validation_error:
            return VerifyResponse(isValid=False, invalidReason=validation_error)

        # Verify EIP-712 signature
        is_valid = await self._verify_signature(
            permit,
            payload.payload.signature,
            requirements.network,
        )

        if not is_valid:
            return VerifyResponse(isValid=False, invalidReason="invalid_signature")

        return VerifyResponse(isValid=True)

    async def settle(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Execute payment settlement on EVM"""
        verify_result = await self.verify(payload, requirements)
        if not verify_result.is_valid:
            return SettleResponse(
                success=False,
                errorReason=verify_result.invalid_reason,
                network=requirements.network,
            )

        permit = payload.payload.payment_permit
        signature = payload.payload.signature

        if permit.meta.kind == PAYMENT_AND_DELIVERY:
            tx_hash = await self._settle_with_delivery(permit, signature, requirements)
        else:
            tx_hash = await self._settle_payment_only(permit, signature, requirements)

        if tx_hash is None:
            return SettleResponse(
                success=False,
                errorReason="transaction_failed",
                network=requirements.network,
            )

        await self._signer.wait_for_transaction_receipt(tx_hash)

        return SettleResponse(
            success=True,
            transaction=tx_hash,
            network=requirements.network,
        )

    def _validate_permit(self, permit: Any, requirements: PaymentRequirements) -> str | None:
        """Validate permit against requirements. Returns error reason or None if valid."""
        if int(permit.payment.max_pay_amount) < int(requirements.amount):
            return "amount_mismatch"

        if permit.payment.pay_to.lower() != requirements.pay_to.lower():
            return "payto_mismatch"

        if permit.payment.pay_token.lower() != requirements.asset.lower():
            return "token_mismatch"

        now = int(time.time())
        if permit.meta.valid_before < now:
            return "expired"

        if permit.meta.valid_after > now:
            return "not_yet_valid"

        return None

    async def _verify_signature(
        self,
        permit: Any,
        signature: str,
        network: str,
    ) -> bool:
        """Verify EIP-712 signature"""
        permit_address = NetworkConfig.get_payment_permit_address(network)
        chain_id = NetworkConfig.get_chain_id(network)
        
        message = convert_permit_to_eip712_message(permit)
        
        return await self._signer.verify_typed_data(
            address=permit.buyer,
            domain={
                "name": "PaymentPermit",
                "chainId": chain_id,
                "verifyingContract": permit_address,
            },
            types=get_payment_permit_eip712_types(),
            message=message,
            signature=signature,
        )

    async def _settle_payment_only(
        self,
        permit: Any,
        signature: str,
        requirements: PaymentRequirements,
    ) -> str | None:
        """Settle payment only (no on-chain delivery)"""
        return await self._signer.write_contract(
            contract_address=NetworkConfig.get_payment_permit_address(requirements.network),
            abi=get_abi_json(PAYMENT_PERMIT_ABI),
            method="permitTransferFrom",
            args=[
                permit.model_dump(by_alias=True),
                permit.buyer,
                signature,
                "0x0000000000000000000000000000000000000000",
                "0x" + "00" * 32,
                "0x",
            ],
        )

    async def _settle_with_delivery(
        self,
        permit: Any,
        signature: str,
        requirements: PaymentRequirements,
    ) -> str | None:
        """Settle with on-chain delivery via merchant contract"""
        return await self._signer.write_contract(
            contract_address=requirements.pay_to,
            abi=get_abi_json(MERCHANT_ABI),
            method="settle",
            args=[permit.model_dump(by_alias=True), signature],
        )
