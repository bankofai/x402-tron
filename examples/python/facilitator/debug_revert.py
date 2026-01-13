#!/usr/bin/env python3
"""Debug script to check why permitTransferFrom reverts"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tronpy import Tron
from tronpy.keys import PrivateKey
import time

# Load environment
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from x402.config import NetworkConfig

# Setup
TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
pk = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY))
buyer = pk.public_key.to_base58check_address()

PAYMENT_PERMIT_ADDRESS = NetworkConfig.get_payment_permit_address("tron:nile")
client = Tron(network="nile")
contract = client.get_contract(PAYMENT_PERMIT_ADDRESS)

# Test parameters
nonce = int(time.time())
kind = 0
payment_id = bytes.fromhex("d12947ecf14ab14840eb2ab5caa497e5")
valid_after = 0
valid_before = int(time.time()) + 3600

print("=" * 60)
print("Checking contract conditions:")
print("=" * 60)

# 1. Check kind
print(f"\n1. Kind check (must be 0):")
print(f"   kind = {kind}")
print(f"   ✓ PASS" if kind == 0 else f"   ✗ FAIL")

# 2. Check timestamp
current_time = int(time.time())
print(f"\n2. Timestamp check:")
print(f"   current_time = {current_time}")
print(f"   valid_after = {valid_after}")
print(f"   valid_before = {valid_before}")
print(f"   ✓ PASS" if valid_after <= current_time <= valid_before else f"   ✗ FAIL")

# 3. Check caller
caller = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"  # TRON zero address
msg_sender = buyer
print(f"\n3. Caller check:")
print(f"   caller = {caller}")
print(f"   msg.sender = {msg_sender}")
print(f"   caller == zero_address: {caller == 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb'}")
print(f"   ✓ PASS (caller is zero address, so check is skipped)")

# 4. Check amount
max_pay_amount = 1000000
transfer_amount = 1000000
print(f"\n4. Amount check (transfer_amount <= max_pay_amount):")
print(f"   transfer_amount = {transfer_amount}")
print(f"   max_pay_amount = {max_pay_amount}")
print(f"   ✓ PASS" if transfer_amount <= max_pay_amount else f"   ✗ FAIL")

# 5. Check nonce
print(f"\n5. Nonce check:")
print(f"   nonce = {nonce}")
nonce_used = contract.functions.nonceUsed(buyer, nonce)
print(f"   nonceUsed(buyer, nonce) = {nonce_used}")
print(f"   ✓ PASS (nonce not used yet)" if not nonce_used else f"   ✗ FAIL (nonce already used)")

# 6. Check token balance and allowance
print(f"\n6. Token balance and allowance check:")
token_address = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"
token = client.get_contract(token_address)
balance = token.functions.balanceOf(buyer)
allowance = token.functions.allowance(buyer, PAYMENT_PERMIT_ADDRESS)
print(f"   buyer = {buyer}")
print(f"   balance = {balance}")
print(f"   allowance = {allowance}")
print(f"   ✓ PASS" if balance >= transfer_amount and allowance >= transfer_amount else f"   ✗ FAIL")

print("\n" + "=" * 60)
