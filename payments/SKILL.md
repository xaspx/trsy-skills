---
name: trsy-payments
description: "Send SOL/USDC from wallet and swap SOL\u2192USDC via Jupiter on Solana. Hermes skill for TRSY."
tags: [trsy, payments, send, solana, usdc, swap, jupiter]
triggers:
  - send sol
  - send usdc
  - swap sol to usdc
  - jupiter swap
  - solana transfer
  - kirim sol
  - kirim usdc
  - tukar sol ke usdc
  - trsy payments
---

# TRSY Payments \u2014 Solana Payment & Swap Skill

Send SOL, send USDC, and swap SOL\u2192USDC via Jupiter. Standalone Python script that works with Hermes wallet-manager session or directly via `SOLANA_KEYPAIR` environment variable.

## Commands

```bash
python3 payments.py balance [wallet_address]
python3 payments.py send-sol <recipient> <amount_sol> [keypair_path]
python3 payments.py send-usdc <recipient> <amount_usdc> [keypair_path]
python3 payments.py quote-swap <amount_sol> [slippage_bps]
python3 payments.py swap-sol-usdc <amount_sol> [slippage_bps] [keypair_path]
python3 payments.py wallet-list
```

## Wallet Resolution Order

1. Direct argument \u2014 keypair path passed as last arg
2. `SOLANA_KEYPAIR` env var
3. Hermes unlocked session
4. Solana CLI config

## Requirements

- Python 3.11+ with `solders`, `base58`, `requests`
- Solana CLI + SPL Token CLI
- `curl` for RPC calls

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SOLANA_KEYPAIR` | Path to keypair JSON |
| `HELIUS_API_KEY` | Helius RPC key |

## Security Notes

- Private keys never logged
- Slippage default 0.5% (50 bps)
- Helius RPC recommended for production

## Examples

```
User: "kirim 0.1 SOL ke EKziLfBf3bpPom2N..."
Agent: python3 payments.py send-sol EKziLfBf3bpPom2N... 0.1

User: "swap 0.5 SOL ke USDC"
Agent: python3 payments.py swap-sol-usdc 0.5

User: "cek balance wallet"
Agent: python3 payments.py balance
```
