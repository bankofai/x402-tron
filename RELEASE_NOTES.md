# Release Notes - v0.1.4

**Release Date:** February 4, 2026

## Overview

First stable release of x402-tron, a TRON implementation of the x402 payment protocol. Enables internet-native, pay-per-request APIs on TRON blockchain with minimal integration effort.

## What's Included

### Python SDK (v0.1.4)
- Complete server, client, and facilitator implementations
- FastAPI integration with `x402_protected` decorator
- Automatic payment verification and settlement
- TIP-712 signature support

### TypeScript SDK (v0.1.4)
- Client SDK with automatic HTTP 402 handling
- TronWeb integration
- Token approval management
- Full TypeScript support

## Key Features

- **Multi-Network Support**: TRON Mainnet, Nile, Shasta
- **Trust-Minimizing**: Facilitator cannot move funds outside client authorization
- **Easy Integration**: One decorator for Python, automatic 402 handling for TypeScript
- **Production Ready**: Comprehensive tests and documentation

## Examples

Complete working examples available at: [x402-tron-demo](https://github.com/open-aibank/x402-tron-demo)

## Documentation

- [README](./README.md)
- [Python SDK](./python/x402/README.md)
- [TypeScript SDK](./typescript/README.md)

## Known Limitations

- Python package not yet published to PyPI (install from source)
- TypeScript package requires TronWeb 5.0+

## Support

- **Issues**: https://github.com/open-aibank/x402-tron/issues
- **Documentation**: https://github.com/open-aibank/x402-tron#readme

## License

MIT License
