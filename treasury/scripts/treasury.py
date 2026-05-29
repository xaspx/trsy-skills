#!/usr/bin/env python3
"""
TRSY Treasury — Solana Wallet Balance & Transaction History
Standalone script. No external dependencies beyond stdlib.

Usage:
    python3 treasury.py <wallet_address>
    HELIUS_RPC=https://rpc.helius.xyz/?api-key=xxx python3 treasury.py <wallet_address>
"""

import json, os, sys, time, urllib.request, urllib.error

RPC_URL = os.environ.get("HELIUS_RPC", "https://api.mainnet-beta.solana.com")
JUPITER_PRICE_URL = "https://price.jup.ag/v6/price?ids=SOL"

KNOWN_TOKENS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": ("USDC", 6, "$"),
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": ("USDT", 6, "$"),
    "So11111111111111111111111111111111111111112": ("wSOL", 9, "\u25ce"),
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": ("BONK", 5, ""),
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": ("WIF", 6, "$"),
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": ("POPCAT", 6, "$"),
    "ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82": ("BOME", 6, "$"),
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": ("JUP", 6, "$"),
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": ("mSOL", 9, "\u25ce"),
    "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL": ("JTO", 6, "$"),
}

def rpc_call(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if "error" in data:
            return None
        return data.get("result")
    except Exception:
        return None

def http_get(url):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def fmt_amount(amount, decimals):
    return int(amount) / (10 ** decimals)

def fmt(n, decimals=2):
    if isinstance(n, float) and n == int(n):
        n = int(n)
    return f"{n:,.{decimals}f}" if isinstance(n, float) else f"{n:,}"

def time_ago(ts):
    diff = int(time.time()) - ts
    if diff < 60: return f"{diff}s ago"
    if diff < 3600: return f"{diff//60}m ago"
    if diff < 86400: return f"{diff//3600}h ago"
    return f"{diff//86400}d ago"

def show(wallet):
    width = 50
    sep = "\u2500" * width
    short = f"{wallet[:6]}...{wallet[-3:]}" if len(wallet) > 10 else wallet
    print(f"\n  {'\u2500' * width}")
    print(f"  \u2550\u2550 TRSY Treasury \u2550\u2550")
    print(f"  Wallet: {wallet}")
    print(f"  {sep}")
    sol_r = rpc_call("getBalance", [wallet])
    if sol_r:
        sol = sol_r.get("value", 0) / 1e9
        print(f"  \u25ce SOL Balance:  {fmt(sol, 4)} SOL")
    else:
        print(f"  \u25ce SOL Balance:  <error>")
        sol = None
    time.sleep(0.3)
    tokens_r = rpc_call("getTokenAccountsByOwner", [wallet, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}])
    tokens_found = []
    if tokens_r:
        for acct in tokens_r.get("value", []):
            try:
                info = acct["account"]["data"]["parsed"]["info"]
                mint = info["mint"]
                raw = info["tokenAmount"]["amount"]
                dec = info["tokenAmount"]["decimals"]
                qty = fmt_amount(raw, dec)
                if qty <= 0: continue
                known = KNOWN_TOKENS.get(mint)
                if known:
                    tokens_found.append((known[0], qty, known[1], known[2]))
                else:
                    tokens_found.append((mint[:8], qty, dec, ""))
            except Exception:
                continue
    price_d = http_get(JUPITER_PRICE_URL)
    price = float(price_d["data"]["SOL"]["price"]) if price_d and price_d.get("data", {}).get("SOL") else None
    if price and sol:
        usd_value = sol * price
        print(f"    \u2514\u2500 USD Value:  ${fmt(usd_value, 2)}  (SOL @ ${fmt(price, 2)})")
    elif price:
        print(f"  SOL Price:      ${fmt(price, 2)}")
    if tokens_found:
        print(f"  {sep}")
        print(f"  Token Balances:")
        for sym, qty, dec, prefix in sorted(tokens_found, key=lambda x: -x[1]):
            if prefix == "$":
                print(f"    ${fmt(qty, 2)} {sym}")
            elif prefix == "\u25ce":
                print(f"    \u25ce {fmt(qty, 4)} {sym}")
            else:
                print(f"    {fmt(qty, 2)} {sym}")
    print(f"  {sep}")
    txs = rpc_call("getSignaturesForAddress", [wallet, {"limit": 10}])
    if txs:
        print(f"  Recent Transactions ({len(txs)}):")
        for i, tx in enumerate(txs, 1):
            sig = tx.get("signature", "")
            ts = tx.get("blockTime")
            ago = time_ago(ts) if ts else "?"
            status = "\u2713" if tx.get("confirmationStatus") == "finalized" else "\u22ef"
            print(f"    {i}. {ago}  {status}  {sig[:8]}...")
    else:
        print(f"  Recent Transactions:  <none or error>")
    print(f"  {sep}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"  {'\u2500' * width}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 treasury.py <wallet_address>", file=sys.stderr)
        sys.exit(1)
    show(sys.argv[1].strip())