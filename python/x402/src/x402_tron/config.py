"""
X402 Network Configuration
Centralized configuration for contract addresses and network settings
"""

from typing import Dict

from x402_tron.exceptions import UnsupportedNetworkError


class NetworkConfig:
    """Network configuration for contract addresses and chain IDs"""

    # Default networks
    TRON_MAINNET = "tron:mainnet"
    TRON_SHASTA = "tron:shasta"
    TRON_NILE = "tron:nile"

    # TRON Chain IDs (EVM chain IDs are parsed from the network string)
    CHAIN_IDS: Dict[str, int] = {
        "tron:mainnet": 728126428,  # 0x2b6653dc
        "tron:shasta": 2494104990,  # 0x94a9059e
        "tron:nile": 3448148188,  # 0xcd8690dc
    }

    # PaymentPermit contract addresses
    PAYMENT_PERMIT_ADDRESSES: Dict[str, str] = {
        "tron:mainnet": "TT8rEWbCoNX7vpEUauxb7rWJsTgs8vDLAn",
        "tron:shasta": "TR2XninQ3jsvRRLGTifFyUHTBysffooUjt",
        "tron:nile": "TFxDcGvS7zfQrS1YzcCMp673ta2NHHzsiH",
        # EVM PaymentPermit addresses (placeholder — not yet deployed)
        # "eip155:8453": "0x...",  # Base
        # "eip155:1": "0x...",     # Ethereum Mainnet
    }

    @classmethod
    def get_chain_id(cls, network: str) -> int:
        """Get chain ID for network

        Args:
            network: Network identifier (e.g., "tron:nile", "eip155:8453")

        Returns:
            Chain ID as integer

        Raises:
            UnsupportedNetworkError: If network is not supported
        """
        # EVM networks encode chain ID directly in the identifier
        if network.startswith("eip155:"):
            try:
                return int(network.split(":", 1)[1])
            except (ValueError, IndexError):
                raise UnsupportedNetworkError(f"Invalid EVM network: {network}")

        chain_id = cls.CHAIN_IDS.get(network)
        if chain_id is None:
            raise UnsupportedNetworkError(f"Unsupported network: {network}")
        return chain_id

    @classmethod
    def get_payment_permit_address(cls, network: str) -> str:
        """Get PaymentPermit contract address for network

        Args:
            network: Network identifier (e.g., "tron:nile", "eip155:8453")

        Returns:
            Contract address (Base58 for TRON, 0x-hex for EVM)
        """
        addr = cls.PAYMENT_PERMIT_ADDRESSES.get(network)
        if addr is not None:
            return addr
        # EVM fallback: zero address
        if network.startswith("eip155:"):
            return "0x0000000000000000000000000000000000000000"
        return "T0000000000000000000000000000000"
