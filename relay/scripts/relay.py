#!/usr/bin/env python3
"""
TRSY Relay - Cross-chain settlement via relay.link
Standalone swap, bridge, and deposit address tool.
"""
import sys, os, json, subprocess

RELAY_API = "https://api.relay.link"
SOLANA_CHAIN_ID, BASE_CHAIN_ID, ARBITRUM_CHAIN_ID = 792703809, 8453, 42161
ETHEREUM_CHAIN_ID, OPTIMISM_CHAIN_ID, POLYGON_CHAIN_ID, BNB_CHAIN_ID = 1, 10, 137, 56

CHAIN_NAMES = {792703809: "Solana", 8453: "Base", 42161: "Arbitrum", 1: "Ethereum", 10: "Optimism", 137: "Polygon", 56: "BNB Chain"}

# Token addresses
SOLANA_WRAPPED_SOL = "So11111111111111111111111111111111111111112"
SOLANA_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ARBITRUM_USDC = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"

TOKEN_ALIASES = {"sol": SOLANA_WRAPPED_SOL, "wsol": SOLANA_WRAPPED_SOL, "usdc_sol": SOLANA_USDC, "usdc_base": BASE_USDC, "usdc_arb": ARBITRUM_USDC}
CHAIN_ALIASES = {"solana": SOLANA_CHAIN_ID, "sol": SOLANA_CHAIN_ID, "base": BASE_CHAIN_ID, "arbitrum": ARBITRUM_CHAIN_ID, "arb": ARBITRUM_CHAIN_ID, "ethereum": ETHEREUM_CHAIN_ID, "eth": ETHEREUM_CHAIN_ID}

def resolve_chain(val):
    val_str = str(val).lower().strip()
    if val_str in CHAIN_ALIASES: return CHAIN_ALIASES[val_str]
    try: return int(val_str)
    except ValueError: return val

def resolve_token(val):
    val_lower = str(val).lower().strip()
    if val_lower in TOKEN_ALIASES: return TOKEN_ALIASES[val_lower]
    return val

def get_wallet_session():
    wallet_dir = os.environ.get("WALLET_DIR", os.path.expanduser("~/.hermes/wallets"))
    session_file = os.path.join(wallet_dir, ".session.json")
    if not os.path.exists(session_file): return None
    with open(session_file) as f: return json.load(f)

def get_api_key():
    return os.environ.get("RELAY_API_KEY", "")

def _curl(method, url, data=None, headers=None):
    cmd = ["curl", "-s", "-X", method, url, "-H", "Content-Type: application/json"]
    if headers:
        for k, v in headers.items(): cmd += ["-H", f"{k}: {v}"]
    if data is not None: cmd += ["-d", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try: return json.loads(result.stdout.strip()) if result.stdout.strip() else {}
    except json.JSONDecodeError: return {"raw": result.stdout.strip(), "error": "parse_failed"}

def relay_api(endpoint, data=None, method="POST"):
    url = f"{RELAY_API}{endpoint}"
    headers = {}
    api_key = get_api_key()
    if api_key: headers["Authorization"] = f"Bearer {api_key}"
    return _curl(method, url, data=data, headers=headers)

def chain_name(cid):
    return CHAIN_NAMES.get(cid, str(cid))

def format_amount(amt_str, decimals):
    try:
        val = int(amt_str) / (10 ** decimals)
        if val == 0: return "0"
        if val >= 0.001: return f"{val:.6f}".rstrip("0").rstrip(".")
        return f"{val:.10f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return amt_str

def print_fees(fees):
    if not fees: return
    print("\nFees:")
    for fee_type in ["gas", "relayer", "relayerGas", "relayerService", "app"]:
        fee = fees.get(fee_type)
        if not fee: continue
        amt = format_amount(fee.get("amount", "0"), fee.get("currency", {}).get("decimals", 0))
        sym = fee.get("currency", {}).get("symbol", "?")
        usd = fee.get("amountUsd", "")
        usd_str = f" (\${usd})" if usd and usd != "0" else ""
        print(f"  {fee_type:15s}: {amt} {sym}{usd_str}")

def print_steps_summary(steps):
    if not steps: return
    print(f"\nRoute: {len(steps)} step(s)")
    for i, step in enumerate(steps, 1):
        kind = step.get("kind", "?")
        print(f"  Step {i}: {kind}")
        items = step.get("items", [])
        for item in items:
            status = item.get("status", "unknown")
            req_id = item.get("requestId", "")
            print(f"    Status: {status}")
            if req_id: print(f"    Request ID: {req_id}")

def cmd_check_chains():
    resp = relay_api("/chains", method="GET")
    chains = resp.get("chains", [])
    if not chains:
        print("\u274c Failed to fetch chains")
        return
    print(f"\nRelay supports {len(chains)} chains\n")
    key_ids = {SOLANA_CHAIN_ID, BASE_CHAIN_ID, ARBITRUM_CHAIN_ID, ETHEREUM_CHAIN_ID, OPTIMISM_CHAIN_ID, POLYGON_CHAIN_ID, BNB_CHAIN_ID}
    print("Key chains (Solana + top EVM):")
    for c in chains:
        if c.get("id") in key_ids:
            solver = [s.get("symbol", "") for s in c.get("solverCurrencies", [])[:6]]
            print(f"  {c['displayName']:20s} ID={c['id']:10d}  VM={c.get('vmType','?'):6s}  Solvers: {', '.join(solver)}")

def cmd_quote_same_chain(amount_sol, wallet=None):
    if not wallet:
        session = get_wallet_session()
        if session: wallet = session.get("address", "")
        else: wallet = "So11111111111111111111111111111111111111112"
    data = {"user": wallet, "originChainId": SOLANA_CHAIN_ID, "destinationChainId": SOLANA_CHAIN_ID,
            "originCurrency": SOLANA_WRAPPED_SOL, "destinationCurrency": SOLANA_USDC,
            "amount": str(int(float(amount_sol) * 1e9)), "tradeType": "EXACT_INPUT"}
    resp = relay_api("/quote", data)
    if "error" in resp:
        print(f"\u274c {resp.get('error')}")
        return
    print(f"\n\u2705 Quote received: {amount_sol} SOL \u2192 USDC on Solana")
    print_steps_summary(resp.get("steps", []))
    print_fees(resp.get("fees", {}))

def cmd_quote_cross_chain(amount_str, origin_chain, dest_chain, origin_token, dest_token, wallet=None):
    if not wallet:
        session = get_wallet_session()
        wallet = session.get("address", "") if session else "So11111111111111111111111111111111111111112"
    oc, dc = resolve_chain(origin_chain), resolve_chain(dest_chain)
    ot, dt = resolve_token(origin_token), resolve_token(dest_token)
    data = {"user": wallet, "originChainId": oc, "originCurrency": ot,
            "destinationChainId": dc, "destinationCurrency": dt,
            "amount": str(amount_str), "recipient": wallet, "tradeType": "EXACT_INPUT"}
    resp = relay_api("/quote", data)
    if "error" in resp:
        print(f"\u274c {resp.get('error')}")
        return
    print(f"\n\u2705 Quote received")
    print_steps_summary(resp.get("steps", []))
    print_fees(resp.get("fees", {}))

def cmd_deposit_address(amount_str, origin_chain, dest_chain, origin_token, dest_token, wallet=None):
    if not get_api_key():
        print("\u274c Deposit addresses require a Relay API key.\nSet RELAY_API_KEY env var.")
        return
    if not wallet:
        session = get_wallet_session()
        if session: wallet = session.get("address", "")
        else: print("\u274c No wallet session"); return
    oc, dc = resolve_chain(origin_chain), resolve_chain(dest_chain)
    ot, dt = resolve_token(origin_token), resolve_token(dest_token)
    data = {"user": wallet, "originChainId": oc, "originCurrency": ot,
            "destinationChainId": dc, "destinationCurrency": dt,
            "amount": str(amount_str), "recipient": wallet, "tradeType": "EXACT_INPUT"}
    resp = relay_api("/intents", data)
    if "error" in resp:
        print(f"\u274c {resp.get('error')}")
        return
    print(f"\n\u2705 Deposit address generated!")
    print(f"   Address: {resp.get('depositAddress', 'N/A')}")
    print(f"   Request ID: {resp.get('requestId', 'N/A')}")

def cmd_status(request_id):
    resp = relay_api(f"/intents/status?requestId={request_id}", method="GET")
    if "error" in resp: print(f"\u274c {resp['error']}"); return
    print(f"Intent {request_id[:16]}...: {resp.get('status', 'unknown')}")

def cmd_routes():
    print("Available SOL \u2194 USDC Routes:\n")
    print("Same-chain (Solana): SOL \u2192 USDC via Jupiter")
    print("Cross-chain: Solana USDC \u2194 Base/Arbitrum USDC")
    print("Deposit: Needs RELAY_API_KEY")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "check-chains": cmd_check_chains()
    elif cmd == "routes": cmd_routes()
    elif cmd == "quote-same":
        amount = sys.argv[2] if len(sys.argv) > 2 else "0.01"
        cmd_quote_same_chain(amount)
    elif cmd == "quote-cross":
        if len(sys.argv) < 6: print("Usage: quote-cross <amount> <from_chain> <to_chain> <from_token> <to_token>"); return
        cmd_quote_cross_chain(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "sol")
    elif cmd == "deposit-address":
        if len(sys.argv) < 6: print("Usage: deposit-address <amount> <from_chain> <from_token> <to_chain> <to_token>"); return
        cmd_deposit_address(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "usdc_sol")
    elif cmd == "status":
        if len(sys.argv) < 3: print("Usage: status <request_id>"); return
        cmd_status(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
