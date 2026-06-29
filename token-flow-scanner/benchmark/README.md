# Token Flow Scanner — Benchmark

- **完整分析与候选**：见 [BENCHMARK_CANDIDATES.md](./BENCHMARK_CANDIDATES.md)（按 taxonomy 分类、每类 1~2 典型、负样本/hold-out 建议）
- **设计规范**：见 [../docs/BENCHMARK_SPEC.md](../docs/BENCHMARK_SPEC.md)（阶段 1 创建）
- **标注表**：`benchmark_labels.csv`（已按 BENCHMARK_CANDIDATES 预填 18 正样本 + 5 hold-out）
- **候选与筛选**：`benchmark_candidates.csv`
- **标注操作**：用 [../docs/annotation_template.md](../docs/annotation_template.md) 逐条填，再合并到 `benchmark_labels.csv`
- **Case 与漏洞合约源码**：见 [cases/README.md](./cases/README.md)。每个 case 含链、漏洞合约地址、PoC 路径；源码需运行 `python3 token-flow-scanner/benchmark/scripts/fetch_contract_sources.py`（需联网）从 BSCScan/Etherscan/Basescan/Arbiscan 拉取，或按 `NOT_VERIFIED.txt` 中的链接手动复制。

## 正样本与 hold-out

- **正样本**：18 个，覆盖 T01–T11（T12 待补）；每类 1~2 个，均有 PoC。
- **Hold-out**：5 个（Penpiexyzio、PRXVT、LAURAToken、WETC_Token、RANTToken），仅用于最终评估。
- **负样本**：仓库无现成，需自建或外选；见 BENCHMARK_CANDIDATES.md 第三节。

## 运行 PoC（示例）

在 DeFiHackLabs 根目录：

```bash
forge test --contracts ./src/test/2026-01/MTToken_exp.sol -vvv
forge test --contracts ./src/test/2023-11/3913_exp.sol -vvv
```

（具体参数以各 `_exp.sol` 的 forge 配置为准；需 fork 的见各 case 注释或 past/*/README.md。）
