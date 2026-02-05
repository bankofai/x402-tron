"""
UptoTronClientMechanism - TRON client mechanism for "upto" payment scheme
"""

from x402_tron.address import AddressConverter, TronAddressConverter
from x402_tron.mechanisms.client.base_upto import BaseUptoClientMechanism


class UptoTronClientMechanism(BaseUptoClientMechanism):
    """TRON client mechanism for upto payment scheme"""

    def _get_address_converter(self) -> AddressConverter:
        return TronAddressConverter()
