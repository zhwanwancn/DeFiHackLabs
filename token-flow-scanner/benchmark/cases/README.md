# Benchmark case 目录

每个 case 对应 BENCHMARK_CANDIDATES 中的一个 PoC，用于存放**漏洞合约源码**，供 Token Flow Scanner 扫描。

## 目录结构

```
cases/
├── README.md           # 本说明
├── manifest.json       # (chain, address, poc 路径) 列表
├── T01_202601_MTToken/   # 目录名=前缀_YYYYMM_名称，从 manifest id 与 date 生成
│   ├── README.md
│   ├── MetaverseToken.sol
│   └── NOT_VERIFIED.txt
├── T15_202503_Pump/
├── ...
└── T99_202409_1/        # hold-out：T99_1=Penpie, T99_2=PRXVT, T99_3=LAURA, T99_4=RANT
```

## 获取漏洞合约源码

1. **自动拉取（需联网）**：在仓库根目录执行  
   ```bash
   # 建议设置 API Key 以提高限频、避免 "Max rate limit reached"（可选）
   export ETHERSCAN_API_KEY=你的Key    # Etherscan/Basescan/Arbiscan
   export BSCSCAN_API_KEY=你的Key      # 仅 BSC，不设则用 ETHERSCAN_API_KEY

   python3 token-flow-scanner/benchmark/scripts/fetch_contract_sources.py
   ```  
   脚本在 `benchmark/scripts/` 下，按 `manifest.json` 对 BSCScan / Etherscan / Basescan / Arbiscan 请求 `getsourcecode`（Etherscan API V2），将 verified 源码写入各 case，文件名为 API 返回的合约名（如 `RANTToken.sol`）。**若地址为 Proxy（TransparentUpgradeableProxy、AdminUpgradeabilityProxy 等）**，会通过 RPC 读 implementation 存储槽并拉取实现合约源码。若合约未验证或请求失败，则写入或保留 `NOT_VERIFIED.txt`。无 API Key 时约 1 次/5 秒；有 Key 时可 3–5 次/秒。

2. **手动拉取**：打开 `NOT_VERIFIED.txt` 中的链接，从区块浏览器复制合约源码，保存为对应 case 下的 `{合约名}.sol`（与 API 命名一致，如 `RANTToken.sol`）。

## manifest.json 字段

- `id`：case 目录名。正样本 T01–T15、T17–T18，hold-out T99_1–T99_4（含 Token 与 非Token；已移除 NOT_VERIFIED：futureswap、P719、WETC、YBToken）。  
- `chain`：`bsc` | `mainnet` | `base` | `arbitrum`  
- `address`：漏洞合约地址  
- `name`：合约名称/备注  
- `poc`：PoC 路径，如 `src/test/2026-01/MTToken_exp.sol`  
- `date`：YYYY-MM，从 poc 路径解析（如 `src/test/2026-01/…` → `2026-01`），用于 README、.sol 头部、NOT_VERIFIED；**目录名** 在 manifest `id` 首段后插入 YYYYMM，如 `T01_MTToken`+`2026-01` → `T01_202601_MTToken`，`T99_1`+`2024-09` → `T99_202409_1`。

## 与 benchmark 的对应

- case **T01–T15、T17–T18**（正样本）与 `benchmark_labels.csv` / `BENCHMARK_CANDIDATES.md` 中的 `vuln_types`、`contract_path` 对应。
- **T99_1–T99_4**（hold-out）为最终评估用，不参与 scanner 设计/调参；对应 Penpie、PRXVT、LAURAToken、RANTToken。
