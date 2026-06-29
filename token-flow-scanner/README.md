# Token Flow Scanner

AI 驱动的 Token 智能合约漏洞扫描器，面向通缩币、税费币、奖励类等 ERC20 变体。

- **计划与节奏**：见 [PLAN.md](./PLAN.md)（每日约 2h，目标 3 月底交付）
- **漏洞分类**：见 [docs/taxonomy.md](./docs/taxonomy.md)
- **Benchmark 说明**：见 [benchmark/README.md](./benchmark/README.md)（随阶段 2、5 完善）

## 快速开始（交付后）

```bash
# 安装依赖后
./scanner/run.sh --input path/to/token.sol [--target ContractName]
# 或
python scanner/main.py --input path/to/token.sol
```

## 当前状态

- [x] 项目计划 [PLAN.md](./PLAN.md)
- [ ] 漏洞分类定稿
- [ ] Benchmark 标注完成
- [ ] Scanner MVP
- [ ] 评估与交付
