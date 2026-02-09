"""
Tests for NativeExactTronServerMechanism.
"""

import pytest

from x402_tron.mechanisms.native_exact.server import NativeExactTronServerMechanism
from x402_tron.mechanisms.native_exact.types import SCHEME_NATIVE_EXACT
from x402_tron.tokens import TokenInfo, TokenRegistry
from x402_tron.types import PaymentRequirements


@pytest.fixture(autouse=True)
def _register_test_token():
    TokenRegistry.register_token(
        "tron:nile",
        TokenInfo(address="TTestUSDTAddress", decimals=6, name="Test USDT", symbol="USDT"),
    )
    yield
    TokenRegistry._tokens.get("tron:nile", {}).pop("USDT", None)


@pytest.fixture
def mechanism():
    return NativeExactTronServerMechanism()


class TestScheme:
    def test_scheme(self, mechanism):
        assert mechanism.scheme() == SCHEME_NATIVE_EXACT


class TestParsePrice:
    @pytest.mark.anyio
    async def test_parse_valid_price(self, mechanism):
        result = await mechanism.parse_price("1 USDT", "tron:nile")
        assert result["amount"] == 1_000_000
        assert result["symbol"] == "USDT"
        assert result["decimals"] == 6

    @pytest.mark.anyio
    async def test_parse_fractional_price(self, mechanism):
        result = await mechanism.parse_price("0.5 USDT", "tron:nile")
        assert result["amount"] == 500_000

    @pytest.mark.anyio
    async def test_parse_invalid_format(self, mechanism):
        with pytest.raises(ValueError):
            await mechanism.parse_price("invalid", "tron:nile")


class TestEnhancePaymentRequirements:
    @pytest.mark.anyio
    async def test_adds_token_metadata(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="1000000",
            asset="TTestUSDTAddress",
            payTo="TTestMerchant",
        )
        enhanced = await mechanism.enhance_payment_requirements(req, "PAYMENT_ONLY")
        assert enhanced.extra is not None
        assert enhanced.extra.name == "Test USDT"
        assert enhanced.extra.version == "1"


class TestValidatePaymentRequirements:
    def test_valid_requirements(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="1000000",
            asset="TTestUSDTAddress",
            payTo="TTestMerchant",
        )
        assert mechanism.validate_payment_requirements(req) is True

    def test_invalid_network(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="eip155:1",
            amount="1000000",
            asset="TTestUSDTAddress",
            payTo="TTestMerchant",
        )
        assert mechanism.validate_payment_requirements(req) is False

    def test_invalid_asset_format(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="1000000",
            asset="0xNotTronAddress",
            payTo="TTestMerchant",
        )
        assert mechanism.validate_payment_requirements(req) is False

    def test_invalid_payto_format(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="1000000",
            asset="TTestUSDTAddress",
            payTo="0xNotTronAddress",
        )
        assert mechanism.validate_payment_requirements(req) is False

    def test_zero_amount(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="0",
            asset="TTestUSDTAddress",
            payTo="TTestMerchant",
        )
        assert mechanism.validate_payment_requirements(req) is False

    def test_negative_amount(self, mechanism):
        req = PaymentRequirements(
            scheme="native_exact",
            network="tron:nile",
            amount="-100",
            asset="TTestUSDTAddress",
            payTo="TTestMerchant",
        )
        assert mechanism.validate_payment_requirements(req) is False


class TestVerifySignature:
    @pytest.mark.anyio
    async def test_passthrough_when_permit_none(self, mechanism):
        """native_exact has no permit, verify_signature should pass through"""
        result = await mechanism.verify_signature(None, "0xsig", "tron:nile")
        assert result is True

    @pytest.mark.anyio
    async def test_passthrough_when_permit_present(self, mechanism):
        """Even with a permit object, should pass through"""
        result = await mechanism.verify_signature(object(), "0xsig", "tron:nile")
        assert result is True
