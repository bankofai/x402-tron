/**
 * Payment policies for filtering or reordering payment requirements.
 *
 * Policies are applied in order after mechanism filtering and before token selection.
 */

import { findByAddress } from '../tokens.js';
import type { PaymentRequirements } from '../types/index.js';
import type { ClientSigner, PaymentPolicy } from './x402Client.js';

function getDecimals(req: PaymentRequirements): number {
  const token = findByAddress(req.network, req.asset);
  return token?.decimals ?? 6;
}

/** Callback that resolves a signer for a given scheme+network */
export type SignerResolver = (scheme: string, network: string) => ClientSigner | null;

/**
 * Policy that filters out requirements with insufficient balance.
 *
 * When the server accepts multiple tokens (e.g. USDT and USDD),
 * this policy checks the user's on-chain balance for each option
 * and removes requirements the user cannot afford.
 *
 * Signers are auto-resolved from registered mechanisms via the
 * signerResolver callback passed to apply() by X402Client.
 *
 * Usage:
 *   x402.registerPolicy(new SufficientBalancePolicy());
 *
 * Requirements whose network has no matching signer are kept as-is
 * (not filtered out), so downstream mechanism matching can still work.
 *
 * If all requirements are unaffordable, returns an empty array so the
 * caller can raise an appropriate error.
 */
export class SufficientBalancePolicy implements PaymentPolicy {
  async apply(
    requirements: PaymentRequirements[],
    signerResolver?: SignerResolver,
  ): Promise<PaymentRequirements[]> {
    const affordable: PaymentRequirements[] = [];
    for (const req of requirements) {
      const signer = signerResolver ? signerResolver(req.scheme, req.network) : null;
      if (!signer) {
        // No signer for this network — keep the requirement so mechanism
        // matching can still select it (balance check is best-effort).
        affordable.push(req);
        continue;
      }

      let balance: bigint;
      try {
        balance = await signer.checkBalance(req.asset, req.network);
      } catch {
        // Signer cannot query this network; keep the requirement.
        affordable.push(req);
        continue;
      }

      let needed = BigInt(req.amount);
      if (req.extra?.fee?.feeAmount) {
        needed += BigInt(req.extra.fee.feeAmount);
      }
      const decimals = getDecimals(req);
      const token = findByAddress(req.network, req.asset);
      const symbol = token?.symbol ?? req.asset.slice(0, 8);
      const divisor = 10 ** decimals;
      const hBalance = (Number(balance) / divisor).toFixed(decimals);
      const hNeeded = (Number(needed) / divisor).toFixed(decimals);
      if (balance >= needed) {
        console.log(
          `[x402] ${symbol} on ${req.network}: balance=${hBalance} >= needed=${hNeeded} (OK)`
        );
        affordable.push(req);
      } else {
        console.log(
          `[x402] ${symbol} on ${req.network}: balance=${hBalance} < needed=${hNeeded} (skipped)`
        );
      }
    }
    if (affordable.length === 0) {
      console.error('[x402] All payment requirements filtered: insufficient balance');
    }
    return affordable;
  }
}
