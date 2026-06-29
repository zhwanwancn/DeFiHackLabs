# Token Flow Scanner — 交付清单

> 阶段 5（D29–D31）完善并自测后打勾。

## 可交付物

- [ ] **可执行入口**：`scanner/run.sh` 或 `scanner/main.py`，支持 `--input`、可选 `--target`、`--benchmark-dir`
- [ ] **Benchmark**：`benchmark/benchmark_labels.csv` 填满；`benchmark/README.md` 说明 PoC 跑法、hold-out 与负样本
- [ ] **漏洞分类**：`docs/taxonomy.md` 定稿
- [ ] **评估结果**：`eval/score.py`、`eval/report.md`（含 per-type 指标、负样本 FP、hold-out 结果）
- [ ] **使用说明**：`README.md` 安装、环境变量、示例命令、示例输出

## 自测（交付前）

- [ ] 新目录 `git clone` 后，按 README 安装依赖并 run 1 个 `examples/` 中的案例
- [ ] 对 `benchmark/` 中至少 1 个正样本、1 个负样本跑 scanner，结果与 `benchmark_labels` 预期一致或可解释

## 后续迭代（可选）

- 更多负样本、规则或 taxonomy 类型
- 仓库外同类型合约的泛化测试
- CI 中自动跑 `eval/score` 与 benchmark PoC
