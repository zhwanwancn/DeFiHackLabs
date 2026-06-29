#!/usr/bin/env python3
"""
Fetch verified contract source via Etherscan API V2 (unified multichain).
Reads benchmark/cases/manifest.json, writes {ContractName}.sol into each case folder (e.g. RANTToken.sol).

API 说明：使用 Etherscan API V2，V1 已弃用。格式：
  GET https://api.etherscan.io/v2/api?chainid={id}&module=contract&action=getsourcecode&address=0x...&apikey=可选
  参考: https://docs.etherscan.io/v2-migration

API Key 来源（可选，提高限频、避免 "Max rate limit reached"）：
  1) 环境变量: ETHERSCAN_API_KEY, BSCSCAN_API_KEY, EXPLORER_API_KEY
  2) .env 文件: 在 token-flow-scanner/.env 或项目根 .env 中配置，需 pip install python-dotenv

  V2 下单一 ETHERSCAN_API_KEY 即可访问所有链；BSC 链仍可优先用 BSCSCAN_API_KEY 作兼容。

无 API Key 时限频约 1 次/5 秒，脚本会自动放慢；有 Key 时可 3–5 次/秒。

Proxy 合约：若 getsourcecode 返回的 ContractName 为 TransparentUpgradeableProxy、AdminUpgradeabilityProxy 等，
脚本会通过 RPC eth_getStorageAt 读取 EIP-1967 / OZ 的 implementation 存储槽，再拉取实现合约源码并保存。
需链的 RPC（未设置时使用下列公共 RPC）：MAINNET_RPC_URL, BSC_RPC_URL, BASE_RPC_URL, ARBITRUM_RPC_URL。
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
CASES_DIR = os.path.join(BENCHMARK_DIR, "cases")

# 加载 .env（python-dotenv 可选）
# 顺序: token-flow-scanner/.env -> 项目根 .env -> 当前工作目录
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    p = Path(SCRIPT_DIR).resolve()
    candidates = []
    if len(p.parents) > 1:
        candidates.append(p.parents[1])  # token-flow-scanner
    if len(p.parents) > 2:
        candidates.append(p.parents[2])  # 项目根
    for d in candidates:
        env = d / ".env"
        if env.is_file():
            load_dotenv(env)
            break
    else:
        load_dotenv()  # 未找到则从当前工作目录加载

_load_dotenv()

# Etherscan API V2 统一端点（V1 已弃用，返回 "switch to Etherscan API V2"）
# 参考: https://docs.etherscan.io/v2-migration
V2_BASE = "https://api.etherscan.io/v2/api"
# chain 名称 -> chainid（https://docs.etherscan.io/supported-chains）
CHAIN_TO_ID = {
    "bsc": 56,
    "mainnet": 1,
    "base": 8453,
    "arbitrum": 42161,
}

# 各链默认 RPC（可被 MAINNET_RPC_URL, BSC_RPC_URL, BASE_RPC_URL, ARBITRUM_RPC_URL 覆盖）
DEFAULT_RPC = {
    "mainnet": "https://eth.llamarpc.com",
    "bsc": "https://bsc-dataseed1.binance.org",
    "base": "https://mainnet.base.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
}

# EIP-1967 implementation 槽；OZ AdminUpgradeabilityProxy 等使用的旧槽
EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
OZ_LEGACY_IMPLEMENTATION_SLOT = "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"

def _poc_date(poc: str) -> str:
    """从 poc 路径 (如 src/test/2026-01/MTToken_exp.sol) 提取 YYYY-MM，未匹配则返回空串。"""
    m = re.search(r"(\d{4}-\d{2})", poc or "")
    return m.group(1) if m else ""


def _case_dir_id(cid: str, poc_date: str) -> str:
    """在 case id 的首段后插入 YYYYMM，如 T01_MTToken + 2026-01 -> T01_202601_MTToken；无 date 则返回原 id。"""
    if not (poc_date or "").strip():
        return cid
    parts = (cid or "").split("_", 1)
    if len(parts) < 2:
        return cid
    prefix, rest = parts[0], parts[1]
    yyyymm = (poc_date or "").strip().replace("-", "")
    if len(yyyymm) != 6:
        return cid
    return f"{prefix}_{yyyymm}_{rest}"


def _sol_filename(contract_name: str) -> str:
    """将 API 返回的合约名转为安全文件名，如 RANTToken -> RANTToken.sol，yETH weighted stableswap pool -> yETH_weighted_stableswap_pool.sol"""
    s = re.sub(r'[/\\:*?"<>|\s]+', '_', (contract_name or "").strip()).strip("_")
    return (s or "Contract") + ".sol"


def _get_apikey(chain: str) -> str:
    if chain == "bsc":
        return os.environ.get("BSCSCAN_API_KEY") or os.environ.get("ETHERSCAN_API_KEY") or os.environ.get("EXPLORER_API_KEY") or ""
    return os.environ.get("ETHERSCAN_API_KEY") or os.environ.get("EXPLORER_API_KEY") or ""


def _get_rpc_url(chain: str) -> str:
    env_keys = {"mainnet": "MAINNET_RPC_URL", "bsc": "BSC_RPC_URL", "base": "BASE_RPC_URL", "arbitrum": "ARBITRUM_RPC_URL"}
    return os.environ.get(env_keys.get(chain, "")) or DEFAULT_RPC.get(chain, DEFAULT_RPC["mainnet"])


def _is_proxy_name(name: str) -> bool:
    """是否像 TransparentUpgradeableProxy、AdminUpgradeabilityProxy 等代理合约名"""
    n = (name or "").strip()
    if not n or "Proxy" not in n:
        return False
    return any(k in n for k in ("Upgrade", "Transparent", "Admin", "ERC1967", "EIP1967"))


def _get_implementation_address(chain: str, proxy_address: str) -> Optional[str]:
    """通过 eth_getStorageAt 读取 EIP-1967 / OZ 的 implementation 槽，返回实现合约地址或 None。"""
    rpc = _get_rpc_url(chain)
    # 确保 address 为 0x 前缀
    addr = proxy_address if proxy_address.startswith("0x") else "0x" + proxy_address
    for slot in (EIP1967_IMPLEMENTATION_SLOT, OZ_LEGACY_IMPLEMENTATION_SLOT):
        try:
            body = json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getStorageAt",
                "params": [addr, slot, "latest"],
                "id": 1,
            }).encode()
            req = urllib.request.Request(rpc, data=body, method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            val = data.get("result")
            if isinstance(val, str) and val.startswith("0x") and len(val) >= 42:
                impl = "0x" + val[2:][-40:].lower()
                if impl != "0x0000000000000000000000000000000000000000":
                    return impl
        except Exception:
            continue
    return None


def fetch_source(chain: str, address: str) -> tuple[bool, str, str]:
    """Returns (ok, contract_name, source_content)."""
    chainid = CHAIN_TO_ID.get(chain, 1)
    url = f"{V2_BASE}?chainid={chainid}&module=contract&action=getsourcecode&address={address}"
    key = _get_apikey(chain)
    if key:
        url = f"{url}&apikey={key}"
    req = urllib.request.Request(url, headers={"User-Agent": "TokenFlowScanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return False, "", str(e)

    if data.get("status") != "1":
        msg = data.get("message", "Unknown")
        res = data.get("result", "")
        if isinstance(res, str) and res and res != "OK":
            msg = f"{msg}; result={res}"
        return False, "", msg

    raw_result = data.get("result")
    if not raw_result:
        return False, "", data.get("message", "No result")
    # 未验证时 result 为字符串 "Contract source code not verified"
    if isinstance(raw_result, str):
        return False, "Contract", raw_result
    if not isinstance(raw_result, list) or len(raw_result) < 1:
        return False, "", "Unexpected result format"

    res = raw_result[0]
    name = (res.get("ContractName") or "Unknown").strip() or "Contract"
    raw = (res.get("SourceCode") or "").strip()
    if not raw:
        return False, name, "Contract not verified (SourceCode empty)"

    # Standard single-file
    if not raw.startswith("{"):
        return True, name, raw

    # Multi-file JSON: {"language":"Solidity","sources":{"path":"content"}}
    try:
        inner = json.loads(raw)
    except json.JSONDecodeError:
        return True, name, raw
    if isinstance(inner, dict) and "sources" in inner:
        combined = []
        for path, obj in sorted(inner["sources"].items()):
            content = obj.get("content", "") if isinstance(obj, dict) else str(obj)
            combined.append(f"// --- {path} ---\n{content}")
        return True, name, "\n\n".join(combined)
    # Nested JSON string (double-encoded)
    if isinstance(inner, str) and inner.startswith("{"):
        try:
            inner2 = json.loads(inner)
            if isinstance(inner2, dict) and "sources" in inner2:
                combined = []
                for path, obj in sorted(inner2["sources"].items()):
                    content = obj.get("content", "") if isinstance(obj, dict) else str(obj)
                    combined.append(f"// --- {path} ---\n{content}")
                return True, name, "\n\n".join(combined)
        except json.JSONDecodeError:
            pass
    return True, name, raw


def main():
    manifest_path = os.path.join(CASES_DIR, "manifest.json")
    if not os.path.isfile(manifest_path):
        print("manifest.json not found", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    for i, m in enumerate(items):
        cid = m["id"]
        chain = m["chain"]
        addr = m["address"]
        name = m.get("name", "vuln")
        poc = m.get("poc", "") or ""
        poc_date = (m.get("date") or "").strip() or _poc_date(poc)
        case_dir_id = _case_dir_id(cid, poc_date)
        case_dir = os.path.join(CASES_DIR, case_dir_id)
        os.makedirs(case_dir, exist_ok=True)

        readme = os.path.join(case_dir, "README.md")
        if not os.path.isfile(readme):
            with open(readme, "w", encoding="utf-8") as f:
                f.write(f"# {case_dir_id}\n\n")
                if case_dir_id != cid:
                    f.write(f"- **Case (logical id)**: {cid}\n")
                f.write(f"- **Chain**: {chain}\n")
                f.write(f"- **Vulnerable contract**: `{addr}`\n")
                f.write(f"- **PoC**: `{poc}`\n")
                if poc_date:
                    f.write(f"- **PoC date (YYYY-MM)**: {poc_date}\n")

        existing = list(Path(case_dir).glob("*.sol"))
        if existing:
            print(f"[skip] {case_dir_id} ({existing[0].name} exists)")
            continue

        ok, cname, content = fetch_source(chain, addr)
        # 无 API Key 时限频约 1 次/5 秒；有 Key 时可适当提速
        time.sleep(5.5 if not _get_apikey(chain) else 0.5)

        header_addr = addr
        extra_comment = ""
        if ok and content and _is_proxy_name(cname):
            impl = _get_implementation_address(chain, addr)
            if impl:
                time.sleep(5.5 if not _get_apikey(chain) else 0.5)
                ok2, cname2, content2 = fetch_source(chain, impl)
                time.sleep(5.5 if not _get_apikey(chain) else 0.5)
                if ok2 and content2:
                    cname, content = cname2, content2
                    header_addr = impl
                    extra_comment = f"// Proxy: {addr}\n"

        if ok and content:
            sol_filename = _sol_filename(cname)
            sol_path = os.path.join(case_dir, sol_filename)
            with open(sol_path, "w", encoding="utf-8") as f:
                f.write(f"// Fetched from {chain} {header_addr}\n{extra_comment}// ContractName: {cname}\n")
                if poc_date:
                    f.write(f"// PoC date (YYYY-MM): {poc_date}\n")
                f.write("\n")
                f.write(content)
            not_ver = os.path.join(case_dir, "NOT_VERIFIED.txt")
            if os.path.isfile(not_ver):
                os.remove(not_ver)
            print(f"[ok]   {case_dir_id} -> {sol_filename}")
        else:
            base = {"bsc": "bscscan.com", "mainnet": "etherscan.io", "base": "basescan.org", "arbitrum": "arbiscan.io"}.get(chain, "etherscan.io")
            explorer = f"https://{base}/address/{addr}#code"
            with open(os.path.join(case_dir, "NOT_VERIFIED.txt"), "w", encoding="utf-8") as f:
                f.write(f"Chain: {chain}\nAddress: {addr}\n")
                if poc_date:
                    f.write(f"PoC date (YYYY-MM): {poc_date}\n")
                f.write("\n")
                f.write(f"To fetch: run from repo root:\n  python3 token-flow-scanner/benchmark/scripts/fetch_contract_sources.py\n")
                f.write(f"(requires network). Or manually: {explorer}\n\n")
                if not ok:
                    if "urlopen" in str(content) or "Errno" in str(content):
                        f.write("Last error: network/DNS unreachable. Run this script with internet.\n")
                    else:
                        f.write(f"Last error: {content}\n")
                        if "rate limit" in str(content).lower() or "api key" in str(content).lower():
                            f.write("Tip: set ETHERSCAN_API_KEY or BSCSCAN_API_KEY (see script docstring).\n")
                else:
                    f.write("SourceCode empty or contract not verified on block explorer.\n")
            print(f"[--]   {case_dir_id} NOT_VERIFIED: {content[:80]}")


if __name__ == "__main__":
    main()
