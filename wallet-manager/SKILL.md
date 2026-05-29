---
name: trsy-wallet-manager
description: Standalone Solana wallet management with AES-256-GCM encryption. No dependency on bank-charity.
tags: [trsy, wallet, solana, security]
version: 1.0.0
author: TRSY
commands:
  - wallet-manager create
  - wallet-manager import-private
  - wallet-manager import-mnemonic
  - wallet-manager export
  - wallet-manager list
  - wallet-manager unlock
  - wallet-manager lock
  - wallet-manager audit
  - wallet-manager status
data_path: ~/.hermes/skills-data/trsy/wallets/
dependencies:
  - cryptography>=41.0.0
---

# TRSY Wallet Manager Skill

**trsy-wallet-manager** — Hermes skill for creating, importing, exporting, and managing Solana wallets with AES-256-GCM encrypted storage. Completely standalone: no dependency on `bank-charity` or any other skill.

## Overview

| Property | Value |
|---|---|
| Skill ID | `trsy-wallet-manager` |
| Script | `scripts/wallet-manager.py` |
| Data dir | `~/.hermes/skills-data/trsy/wallets/` |
| Encryption | AES-256-GCM (via `cryptography` package) |
| Key derivation | PBKDF2-HMAC-SHA256 (200,000 iterations) |
| Session TTL | 5 minutes (auto-expire) |
| Wallet type | Ed25519 (Solana) |
| Audit log | JSONL at `wallets/audit.jsonl` |
| Python | stdlib + `cryptography` package only |

## Quick Start

```bash
# Install dependency
pip install cryptography

# Unlock session (5 min window)
python wallet-manager.py unlock

# Create a wallet
python wallet-manager.py create -n my-wallet

# List wallets
python wallet-manager.py list

# Export private key
python wallet-manager.py export my-wallet

# Lock session when done
python wallet-manager.py lock
```

## Security Architecture

### Encryption Flow

```
Password ──→ PBKDF2-HMAC-SHA256 ──→ AES-256-GCM key
                                      │
Private Key Bytes ──────────────────→ AES-GCM.encrypt() ──→ nonce + ciphertext
                                                              (stored as base64)
```

- **AES-256-GCM**: Authenticated encryption — provides both confidentiality and integrity.
- **PBKDF2**: 200,000 iterations of HMAC-SHA256 to derive the encryption key from the password.
- **Random nonce**: 12-byte random nonce per wallet, generated with `secrets.token_bytes()`.
- **Per-wallet encryption**: Each wallet's private key is encrypted independently.
- **Key material never touches disk unencrypted**: Only the encrypted ciphertext is persisted.

### Session Model

```
unlock ──→ /.session file created (mode 0600)
           ├── salt (base64)
           ├── key_check (HMAC-SHA256 integrity tag)
           ├── aes_key (base64) — for fast decrypt
           └── expires_at (UNIX timestamp)

lock ──→ /.session file deleted
auto ──→ expires after 300 seconds; subsequent ops reject
```

### Audit Logging

All sensitive operations are logged to `audit.jsonl`.

The audit log auto-truncates to the last 1000 entries. Log format is newline-delimited JSON (JSONL).

## Commands

### `unlock` — Start Session

Prompts for a password to derive the AES-256 encryption key. Session auto-expires after 5 minutes.

```bash
python wallet-manager.py unlock
```

### `lock` — End Session

Deletes the session file.

```bash
python wallet-manager.py lock
```

### `status` — Check Session & Count

```bash
python wallet-manager.py status
```

### `create` — New Wallet

Generates a fresh Ed25519 keypair and stores it encrypted.

```bash
python wallet-manager.py create -n my-wallet
```

### `import-private` — Import from Base58 Key

Import an existing Solana wallet from a base58-encoded private key.

```bash
python wallet-manager.py import-private "2j2v549GgmqDmvMbwWqMUteKAXvTXBUugGmCxisC1BHNgcpzD44WDMMz4W5rdJrATXyRpLpo23GAhCrnthCmhmCV" -n imported-wallet
```

### `import-mnemonic` — Import from BIP39 Phrase

```bash
python wallet-manager.py import-mnemonic -n my-wallet -p "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
```

### `export` — Export Private Key

```bash
python wallet-manager.py export my-wallet -f base58
python wallet-manager.py export my-wallet -f json
python wallet-manager.py export my-wallet -f hex
```

### `list` — List Wallets

```bash
python wallet-manager.py list
```

### `audit` — Audit Log

```bash
python wallet-manager.py audit --limit 10
```

## Error Handling

| Scenario | Behavior |
|---|---|
| Wallet already exists | Error: "already exists", exit code 1 |
| Wallet not found | Error: "not found", exit code 1 |
| Session not unlocked | Error: "Run 'unlock' first", exit code 1 |
| Session expired | Session file auto-deleted, requires re-unlock |
| Invalid base58 key | Error with specific character, exit code 1 |
| Invalid private key length | Error: "expected 32 or 64 bytes", exit code 1 |
| Invalid mnemonic checksum | Error: "checksum mismatch", exit code 1 |
| Word not in BIP39 list | Error: "'word' is not in the BIP39 English wordlist", exit code 1 |
| Decryption failure (wrong key) | Error: "Decryption failed", exit code 1 |

## Security Notes

1. **Password strength is critical**: The PBKDF2 key derivation is only as strong as the password.
2. **No password recovery**: There is no backdoor, no master key, no password hint storage.
3. **Session files are sensitive**: The `.session` file contains the derived AES key in base64.
4. **Audit log is append-only**: The audit log records all sensitive actions but is not itself encrypted.
5. **BIP39 passphrase**: When using `import-mnemonic`, an optional BIP39 passphrase adds extra security.
6. **No network calls**: This skill is completely offline. No RPC, no API, no external services.

## Development

### File layout
```
wallet-manager/
├── SKILL.md              ← This file
└── scripts/
    └── wallet-manager.py  ← Main CLI script
```
