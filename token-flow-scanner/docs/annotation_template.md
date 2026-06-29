# Benchmark 标注模板

每个合约标注时按下面填，再汇总到 `benchmark/benchmark_labels.csv`。

---

## 合约

- **路径**：（相对于 DeFiHackLabs 根，如 `src/test/2026-01/MTToken_exp.sol`，若只标 token 本体则写 token 路径）
- **PoC**：`forge test --contracts <path> -vvv` 是否通过

## 标签

- **vuln_types**：从 `docs/taxonomy.md` 的 ID 或英文名多选，逗号分隔，如 `T01,T04`
- **is_negative**：0=有漏洞，1=安全/加固样本
- **is_holdout**：0=参与设计/调参，1=仅最终评估

## Root cause（一行，仅正样本）

- 用一句话说明：什么假设被违反、或什么操作序列导致问题。
- 例：`transactionFee() 按多比例分 transactFeeValue 且未约束 sum<=100，pair 等合约成为 fee 目标被超额扣减`

## Notes（可选）

- 依赖的链/RPC、需要 fork 的块、或与 taxonomy 的细微差异。
