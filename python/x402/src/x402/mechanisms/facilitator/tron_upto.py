"""
UptoTronFacilitatorMechanism - "upto" 支付方案的 TRON facilitator 机制
"""

import logging
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
    KIND_MAP,
    PAYMENT_AND_DELIVERY,
)
from x402.utils import (
    normalize_tron_address,
    tron_address_to_evm,
    payment_id_to_bytes,
    convert_permit_to_eip712_message,
    convert_tron_addresses_to_evm,
)

if TYPE_CHECKING:
    from x402.signers.facilitator import FacilitatorSigner

logger = logging.getLogger(__name__)


class UptoTronFacilitatorMechanism(FacilitatorMechanism):
    """"upto" 支付方案的 TRON facilitator 机制"""

    def __init__(
        self,
        signer: "FacilitatorSigner",
        fee_to: str | None = None,
        base_fee: int = 1000000,
    ) -> None:
        self._signer = signer
        self._fee_to = fee_to or signer.get_address()
        self._base_fee = base_fee
        logger.info(f"UptoTronFacilitatorMechanism initialized: fee_to={self._fee_to}, base_fee={base_fee}")

    def scheme(self) -> str:
        return "exact"

    async def fee_quote(
        self,
        accept: PaymentRequirements,
        context: dict[str, Any] | None = None,
    ) -> FeeQuoteResponse:
        """基于 gas 估算计算费用报价"""
        fee_amount = str(self._base_fee)
        logger.info(f"Fee quote requested: network={accept.network}, amount={accept.amount}, fee={fee_amount}")

        return FeeQuoteResponse(
            fee=FeeInfo(
                feeTo=self._fee_to,
                feeAmount=fee_amount,
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
        logger.info(f"Verifying payment: paymentId={permit.meta.payment_id}, buyer={permit.buyer}, amount={permit.payment.max_pay_amount}")

        # Validate permit against requirements
        validation_error = self._validate_permit(permit, requirements)
        if validation_error:
            logger.warning(f"Validation failed: {validation_error}")
            return VerifyResponse(isValid=False, invalidReason=validation_error)

        # Verify EIP-712 signature
        logger.info("Verifying EIP-712 signature...")
        is_valid = await self._verify_signature(
            permit,
            payload.payload.signature,
            requirements.network,
        )

        if not is_valid:
            logger.warning("Invalid signature")
            return VerifyResponse(isValid=False, invalidReason="invalid_signature")

        logger.info("Payment verification successful")
        return VerifyResponse(isValid=True)

    async def settle(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Execute payment settlement on TRON"""
        permit = payload.payload.payment_permit
        logger.info(f"Starting settlement: paymentId={permit.meta.payment_id}, kind={permit.meta.kind}, network={requirements.network}")
        
        verify_result = await self.verify(payload, requirements)
        if not verify_result.is_valid:
            logger.error(f"Settlement failed: verification failed - {verify_result.invalid_reason}")
            return SettleResponse(
                success=False,
                errorReason=verify_result.invalid_reason,
                network=requirements.network,
            )

        signature = payload.payload.signature

        if permit.meta.kind == PAYMENT_AND_DELIVERY:
            logger.info("Settling with delivery via merchant contract...")
            tx_hash = await self._settle_with_delivery(permit, signature, requirements)
        else:
            logger.info("Settling payment only via PaymentPermit contract...")
            tx_hash = await self._settle_payment_only(permit, signature, requirements)

        if tx_hash is None:
            logger.error("Settlement transaction failed: no transaction hash returned")
            return SettleResponse(
                success=False,
                errorReason="transaction_failed",
                network=requirements.network,
            )

        logger.info(f"Transaction broadcast successful: txHash={tx_hash}")
        logger.info("Waiting for transaction receipt...")
        receipt = await self._signer.wait_for_transaction_receipt(tx_hash)
        logger.info(f"Transaction confirmed: {receipt}")

        return SettleResponse(
            success=True,
            transaction=tx_hash,
            network=requirements.network,
        )

    def _validate_permit(self, permit: Any, requirements: PaymentRequirements) -> str | None:
        """Validate permit against requirements. Returns error reason or None if valid."""
        if int(permit.payment.max_pay_amount) < int(requirements.amount):
            logger.warning(f"Amount mismatch: {permit.payment.max_pay_amount} < {requirements.amount}")
            return "amount_mismatch"

        if permit.payment.pay_to != requirements.pay_to:
            logger.warning(f"PayTo mismatch: {permit.payment.pay_to} != {requirements.pay_to}")
            return "payto_mismatch"

        if permit.payment.pay_token != requirements.asset:
            logger.warning(f"Token mismatch: {permit.payment.pay_token} != {requirements.asset}")
            return "token_mismatch"

        now = int(time.time())
        if permit.meta.valid_before < now:
            logger.warning(f"Permit expired: validBefore={permit.meta.valid_before} < now={now}")
            return "expired"

        if permit.meta.valid_after > now:
            logger.warning(f"Permit not yet valid: validAfter={permit.meta.valid_after} > now={now}")
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
        permit_address_evm = tron_address_to_evm(permit_address)
        chain_id = NetworkConfig.get_chain_id(network)
        
        message = convert_permit_to_eip712_message(permit)
        message = convert_tron_addresses_to_evm(message, tron_address_to_evm)
        
        return await self._signer.verify_typed_data(
            address=permit.buyer,
            domain={
                "name": "PaymentPermit",
                "chainId": chain_id,
                "verifyingContract": permit_address_evm,
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
        contract_address = NetworkConfig.get_payment_permit_address(requirements.network)
        logger.info(f"Calling permitTransferFrom on contract={contract_address}")
        
        permit_tuple = self._build_permit_tuple(permit)
        sig_bytes = bytes.fromhex(signature[2:] if signature.startswith("0x") else signature)
        transfer_details = (int(permit.payment.max_pay_amount),)
        buyer = normalize_tron_address(permit.buyer)
        
        args = [permit_tuple, transfer_details, buyer, sig_bytes]
        
        logger.info(f"Calling permitTransferFrom with {len(args)} arguments (PAYMENT_ONLY mode)")
        
        return await self._signer.write_contract(
            contract_address=contract_address,
            abi=get_abi_json(PAYMENT_PERMIT_ABI),
            method="permitTransferFrom",
            args=args,
        )

    async def _settle_with_delivery(
        self,
        permit: Any,
        signature: str,
        requirements: PaymentRequirements,
    ) -> str | None:
        """Settle with on-chain delivery via merchant contract"""
        merchant_address = requirements.pay_to
        logger.info(f"Calling settle on merchant contract={merchant_address}")
        
        permit_tuple = self._build_permit_tuple(permit)
        sig_bytes = bytes.fromhex(signature[2:] if signature.startswith("0x") else signature)
        
        return await self._signer.write_contract(
            contract_address=merchant_address,
            abi=get_abi_json(MERCHANT_ABI),
            method="settle",
            args=[permit_tuple, sig_bytes],
        )

    def _build_permit_tuple(self, permit: Any) -> tuple:
        """Build permit tuple for contract call"""
        payment_id = permit.meta.payment_id
        if isinstance(payment_id, str):
            payment_id = payment_id_to_bytes(payment_id)
        
        buyer = normalize_tron_address(permit.buyer)
        caller = normalize_tron_address(permit.caller)
        pay_token = normalize_tron_address(permit.payment.pay_token)
        pay_to = normalize_tron_address(permit.payment.pay_to)
        fee_to = normalize_tron_address(permit.fee.fee_to)
        receive_token = normalize_tron_address(permit.delivery.receive_token)
        
        return (
            (  # meta tuple
                KIND_MAP.get(permit.meta.kind, 0),
                payment_id,
                int(permit.meta.nonce),
                permit.meta.valid_after,
                permit.meta.valid_before,
            ),
            buyer,
            caller,
            (pay_token, int(permit.payment.max_pay_amount), pay_to),
            (fee_to, int(permit.fee.fee_amount)),
            (receive_token, int(permit.delivery.mini_receive_amount), int(permit.delivery.token_id)),
        )
