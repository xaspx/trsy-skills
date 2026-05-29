# TRSY Skills

Hermes Agent skills for the TRSY — AI Agent Treasury Network.

Install with Hermes CLI:

```bash
hermes skill install https://github.com/xaspx/trsy-skills
```

## Skills

| Skill | Description | Tags |
|-------|-------------|------|
| **wallet-manager** | Create, import, export, and manage Solana wallets with AES-256-GCM encryption | `trsy`, `wallet`, `solana`, `security` |
| **treasury** | Check real-time Solana wallet balance, token holdings, and transaction history | `trsy`, `treasury`, `balance`, `solana` |
| **payments** | Send SOL/USDC and swap SOL→USDC via Jupiter aggregator | `trsy`, `payments`, `send`, `swap`, `jupiter` |
| **relay** | Cross-chain settlement via relay.link — same-chain swaps, deposit addresses, bridging | `trsy`, `relay`, `cross-chain`, `bridge` |

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com)
- Python 3.10+
- Solana CLI + `spl-token` CLI (for payments)
- Helius RPC URL (optional — `HELIUS_RPC` env var)
- Relay API key (optional — `RELAY_API_KEY` env var, needed for deposit addresses)

## Quick Start

```bash
# Install all skills
hermes skill install https://github.com/xaspx/trsy-skills

# Check wallet balance
hermes wallet-manager list

# View treasury
hermes treasury balance <wallet-address>

# Send payment
hermes payments send-sol --to <address> --amount 0.1

# Cross-chain relay
hermes relay check-chains
```

## Repo Structure

```
trsy-skills/
├── README.md
├── .gitignore
├── wallet-manager/
│   ├── SKILL.md
│   └── scripts/
│       └── wallet-manager.py
├── treasury/
│   ├── SKILL.md
│   └── scripts/
│       └── treasury.py
├── payments/
│   ├── SKILL.md
│   └── scripts/
│       └── payments.py
└── relay/
    ├── SKILL.md
    └── scripts/
        └── relay.py

## License

MIT
