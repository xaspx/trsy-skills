---
name: trsy-treasury
tags: [trsy, treasury, balance, solana]
---

# TRSY Treasury Skill

Check real-time Solana wallet balance and transaction history. Standalone script using public RPC endpoints.

## Trigger Conditions

- User asks: "check treasury", "wallet balance <address>", "cek saldo <address>", "treasury status <address>"
- Run via: `python3 scripts/treasury.py <wallet_address>`

## Steps

1. Parse wallet address (base58, 32-44 chars)
2. Fetch SOL balance from RPC (getBalance)
3. Fetch token accounts (getTokenAccountsByOwner) — USDC, USDT, etc.
4. Fetch SOL price from Jupiter price API (v2)
5. Fetch recent transaction signatures (getSignaturesForAddress, limit 10)
6. Decode each tx for type hints where possible
7. Format and display compact output

## Environment Variables

| Variable     | Default                              | Description            |
|--------------|--------------------------------------|------------------------|
| `HELIUS_RPC` | `https://api.mainnet-beta.solana.com`| Solana JSON-RPC endpoint|

## Example Output

```
── TRSY Treasury ──────────────────────────
Wallet: 7...Abc

◎ SOL Balance: 12.345 SOL ($1,851.75)
  USDC: 5,000.00 USDC ($5,000.00)
  USDT: 250.00 USDT ($250.00)
  BONK: 1,234,567 BONK ($18.52)

SOL Price: $150.00

Recent Transactions (10):
  1. 3m ago  Transfer OUT  1.5 SOL  → abc...xyz
  2. 12m ago Transfer IN   500 USDC  ← def...123
  3. 1h ago  Swap          SOL→USDC  2 SOL → 300 USDC
  ...
───────────────────────────────────────────
```

## Dependencies

- Python 3.10+
- `requests` (stdlib `urllib` can substitute)
