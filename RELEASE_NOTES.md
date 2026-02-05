# Release Notes - v0.1.5

**Release Date:** February 5, 2026

## Overview

Major update to x402-tron with critical bug fixes, breaking changes, and improved async support. This release fixes on-chain transaction failures and updates to the latest PaymentPermit contract deployment.

## 🚨 Breaking Changes

### Renamed Mechanisms
- `UptoTronClientMechanism` → `ExactTronClientMechanism`
- `UptoTronFacilitatorMechanism` → `ExactTronFacilitatorMechanism`

**Migration:**
```python
# Old
from x402_tron.mechanisms.client.tron_upto import UptoTronClientMechanism
mechanism = UptoTronClientMechanism(signer)

# New
from x402_tron.mechanisms.client.tron_exact import ExactTronClientMechanism
mechanism = ExactTronClientMechanism(signer)
```

### Facilitator Fee Required
Facilitators must now configure a fee with non-empty `feeTo` address. The `fee` field in `SupportedResponse` is now required.

**Migration:**
```python
# Facilitator must return fee in /supported endpoint
SupportedResponse(
    kinds=[...],
    fee=SupportedFee(
        feeTo="TYourFacilitatorAddress",
        pricing="per_accept"
    )
)
```

### Updated Contract Addresses
PaymentPermit contracts updated to latest deployment:
- **Mainnet**: `THnW1E6yQWgx9P3QtSqWw2t3qGwH35jARg`
- **Shasta**: `TVjYLoXatyMkemxzeB9M8ZE3uGttR9QZJ8`
- **Nile**: `TQr1nSWDLWgmJ3tkbFZANnaFcB5ci7Hvxa`

## ✨ New Features

- **Multi-Network Facilitator**: Facilitators can now support multiple networks (Nile and Mainnet) simultaneously
- **Async Transaction Verification**: All tronpy operations converted to AsyncTron with proper async/await
- **Auto Facilitator Address**: Server automatically fetches facilitator address from `/supported` endpoint

## 🐛 Bug Fixes

- **Critical**: Fixed on-chain transaction failure where `permit.caller` didn't match facilitator address (`msg.sender`)
- Fixed contract ABI to match new PaymentPermit deployment (removed `transferDetails` parameter)
- Fixed all linting and formatting issues
- Fixed test imports to use new mechanism names

## 🔧 Improvements

- Removed unused `max_amount` filter from `PaymentRequirementsFilter`
- Simplified transaction verification to status check only (60s timeout)
- Improved error messages for facilitator configuration validation
- All async operations properly awaited

## 📦 What's Included

### Python SDK (v0.1.5)
- Complete server, client, and facilitator implementations
- FastAPI integration with `x402_protected` decorator
- Automatic payment verification and settlement
- TIP-712 signature support
- Full async support with AsyncTron

### TypeScript SDK (v0.1.5)
- Client SDK with automatic HTTP 402 handling
- TronWeb integration
- Token approval management
- Full TypeScript support
- Updated to use `ExactTronClientMechanism`

## 📚 Documentation

- [README](./README.md)
- [Python SDK](./python/x402/README.md)
- [TypeScript SDK](./typescript/README.md)
- [CHANGELOG](./CHANGELOG.md)

## 🧪 Testing

All tests passing:
- 24 Python tests (asyncio backend)
- All linting checks passed
- All formatting checks passed

## 🔗 Support

- **Issues**: https://github.com/open-aibank/x402-tron/issues
- **Documentation**: https://github.com/open-aibank/x402-tron#readme

## 📄 License

MIT License
