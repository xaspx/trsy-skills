---
name: trsy-relay
tags: [trsy, relay, cross-chain, swap, bridge]
---

# TRSY Relay Skill

Cross-chain settlement via [Relay.link](https://relay.link). Supports same-chain swaps, deposit addresses, and cross-chain bridging.

## Trigger Conditions

| Trigger | Example |
|---------|---------|
| `relay` | "relay quote 0.1 SOL to USDC" |
| `cross-chain` | "cross-chain quote 50 USDC Solana to Base" |
| `deposit address` | "generate deposit address for 10 USDC" |
| `bridge` | "bridge USDC Solana to Arbitrum" |

## Key Chains

| Chain | Relay ID | Type |
|-------|----------|------|
| Solana | 792703809 | SVM |
| Ethereum | 1 | EVM |
| Base | 8453 | EVM |
| Arbitrum | 42161 | EVM |

## Solana Token Addresses

| Token | Address |
|-------|---------|
| SOL (Wrapped) | `So11111111111111111111111111111111111111112` |
| USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| USDT | `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB` |

## API Key Status

| Feature | Needs Key? |
|---------|-----------|
| List chains | No |
| Same-chain quote | No |
| Cross-chain quote | No |
| Deposit address | Yes |

## Execution Flow

```
User intent \u2192 check wallet session \u2192 validate params \u2192 relay operation \u2192 format result
```

## Commands

```
relay.py check-chains
relay.py quote-same <amount>
relay.py quote-cross <amount> <from_chain> <to_chain> <from_token> <to_token>
relay.py deposit-address <amount> <from_chain> <from_token> <to_chain> <to_token>
relay.py status <request_id>
```

## Dependencies

- Python 3.8+
- `curl`
- Environment: `RELAY_API_KEY` (optional)

No external Python packages required.
