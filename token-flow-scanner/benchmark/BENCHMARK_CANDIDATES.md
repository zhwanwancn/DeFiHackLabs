# Token 相关 PoC 分析与 Benchmark 候选

基于 `src/test` 下 `*_exp.sol` 的 PoC，按 **docs/taxonomy.md** 分类，每类选 1~2 个典型，并标出负样本 / hold-out 建议。

---

## 一、按漏洞类型的候选名单

### T01 — fee 比例无界 (fee-logic-unbounded-shares)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2026-01/MTToken_exp.sol` | `transactionFee()` 多比例分配未约束 sum≤100，pair 等合约成 fee 目标被超额扣减；结合 sync/skim 与 swap 抽走 USDT | **典型 1** |

- **Root cause**：多组 `mul(amount, percent).div(100)` 无 `sum(percent)<=100`，且 fee 目标包含 AMM pair。
- **PoC**：`forge test --contracts ./src/test/2026-01/MTToken_exp.sol -vvv`（需 BSC fork）

---

### T02 — fee 单位混用 (fee-unit-mismatch)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2026-01/futureswap_exp.sol` | 按 token 数量算 fee 传入 `FeeManager.addFee`，下游按 bps/weight 解释，导致异常 bps 与资金转出 | ~~典型 1~~ **已移除：NOT_VERIFIED** |

- **Root cause**：`abs(delta)*feeRateWad/1e18` 以 token 为单位，与 `feeBasisPoints` 语义混用。
- **PoC**：需 fork，有完整 E2E。漏洞合约未在区块浏览器验证，已自 benchmark 移除。

---

### T03 — 通缩/税费不兼容 (deflationary-incompatible)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2023-11/3913_exp.sol` | 3913 为通缩币，pair/Dodo 用 `swapExactTokensForTokens` 按 `amount` 核算，未按 `balanceOf` 差量；burnPairs、多级 flash 套利 | **典型 1** |
| `src/test/2024-04/FIL314_exp.sol` | `hourBurn` 通缩，`getAmountOut`+`transfer(address(FIL314), amount)` 当 sell，按 `amount` 假设到账 | **典型 2** |

- **3913 Root cause**：Router/pair 假设 `amount in = 实际到账`，与通缩/扣税不一致。
- **FIL314 Root cause**：transfer 到自身当 sell，与 `getAmountOut` 的 amount 假设不匹配；hourBurn 放大偏差。

---

### T04 — transfer 钩子操纵 (transfer-hook-manipulation)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2024-11/MFT_exp.sol` | `MFT.transfer()` 对 sell 路径在内部 burn 池子余额；向 pair 大额 transfer 触发，再 skim + swap 抽走报价币 | **典型 1** |
| `src/test/2024-10/P719Token_exp.sol` | `transfer(to)==P719` 时按 sell 处理，内部 swap 逻辑 + burn，可被伪造 pair 与 buy/sell 序列拉高价格再撤池 | ~~典型 2~~ **已移除：NOT_VERIFIED** |
| `src/test/2024-12/LABUBU_exp.sol` | `LABUBU.transfer(self, amount)` 在 flash 回调中多次触发，transfer 钩子/反射逻辑使余额虚增，再 exactInputSingle(amountOutMinimum:0) 抽走报价币 | **典型 2** |

- **MFT Root cause**：transfer 内根据 recipient 与上下文实现“卖”并 burn 池内 token，与 AMM 的 reserve/balance 假设冲突。
- **P719 Root cause**：transfer 进 token 自身即触发 sell 与 burn，价格与余额由自定义逻辑驱动，可被自建 pair 操纵。P719 合约未在区块浏览器验证，已自 benchmark 移除。
- **LABUBU Root cause**：transfer 到自身在 token 内触发特殊逻辑（如反射/分红），在 flash 中多次调用虚增己方余额，再 swap 套利。

---

### T05 — 奖励计算错误 (reward-calculation-error)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2025-01/LPMine_exp.sol` | `extractReward` 用 pair 的 balance 参与计算且时间/状态未正确更新，可反复 `extractReward` 多领 | **典型 1** |

- **LPMine Root cause**：`reason : Use pair balance to calculate the reward, and not update the time correctly, so can claim reward more times.`

**备注**：`sorraStaking.sol`（SorStaking）无 `_exp` 后缀，为 PoC 实现，可作 T05 第二候选；Staking/CErc20 相关（如 SWAPPStaking）已移除。

---

### T06 — 重入 (reentrancy)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2023-11/CAROLProtocol_exp.sol` | `sell()` 内兑 WETH，`receive()` 中再调 `CAROLToWETH` 等，在 WETH 回调里重入协议逻辑，`userBalance`/`ethReserved` 等状态未先更新 | **典型 1** |
| `src/test/2024-09/Penpiexyzio_exp.sol` | README：Reentrancy and Reward Manipulation；`claimRewards` 等与自定义 `getRewardTokens`/`rewardIndexesCurrent` 组合，存在重入与 reward 操纵 | **典型 2 / hold-out** |

- **CAROL Root cause**：先 external call（转 WETH）后改 state，`receive` 中可再次 sell/swap，属 CEI 违反。
- **Penpie**：需伪造 Pendle 兼容的 reward 合约与 `claimRewards` 回调，重入与 T05 叠加；实现较复杂，作 hold-out。

---

### T07 — fee-on-transfer 假设错误 (fee-on-transfer-assumption)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2024-05/NORMIE_exp.sol` | NORMIE 为 fee-on-transfer；PoC 用 `SupportingFeeOnTransferTokens`，但协议/池子侧若按 `amountIn`= 到账量会有偏差；launch block 额外 10% 扣减等 | **典型 1** |
| `src/test/2024-03/TGBS_exp.sol` | `_burnBlock`：当 `burnBlock!=block.number` 时，`transfer` 到自身会在 **pair 内** burn；结合 `SupportingFeeOnTransferTokens`，实际到账与 `amount` 假设不一致 | **典型 2** |

- **NORMIE**：典型 fee-on-transfer + 启动期 fee，与 AMM/DEX 假设 `balanceOf` 增量 = `amount` 不符。
- **TGBS Root cause**：pair 在若干 block 对 transfer 做额外 burn，到账与 `amount` 不一致，属 fee-on-transfer 的变种。

---

### T08 — 权限与敏感参数 (access-control-fee-or-reward)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2025-01/98Token_exp.sol` | `reason : Unprotected public function`；`swapContract.swapTokensForTokens` 等可被任意调用，抽走 98 token | **典型 1** |

- **Root cause**：swap/路由或 fee 相关入口无 `onlyOwner`/权限校验，任何人可触发敏感交换或抽走 token。

---

### T09 — 算术溢出与舍入 (arithmetic-overflow-rounding)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2026-01/Truebit_exp.sol` | `getPurchasePrice`/`buyTRU`/`sellTRU` 中 `solveForAmount` 的 `totalSupply * totalSupply` 可 overflow，得到异常 amount 再买卖套利 | **典型 1**（Token 相关：TRU  bonding curve / 买卖逻辑） |
| `src/test/2025-12/yETH_exp.sol` | `virtual_balance`、`vb_prod_sum`、`update_rates`、`rebase` 等组合， rounding / 不安全运算导致资产被抽 | **典型 2** |

- **Truebit Root cause**：`T*T` 在 `totalSupply` 较大时 overflow，进而 `Root - T` 等计算出错，形成套利；与 TRU token 买卖绑定，属 Token 相关。
- **yETH**：README "Unsafe math"；乘除顺序与精度在 rebase/rate 更新中放大误差。

---

### T10 — 价格/储备操纵 (price-oracle-manipulation, reserve/K manipulation)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2025-09/NGP_exp.sol` | NGT `_update()` 内调 `sync()`，在特定 swap 序列下可操纵 pair 储备与价格，再高价卖出 NGP | **典型 1** |
| `src/test/2025-05/KRCToken_pair_exp.sol` | KRC 为 fee-on-transfer；`transfer`+`skim` 多次使 pair 的 reserve 与真实 `balanceOf` 不同步，再 `swap` 抽走 USDT | **典型 2** |
| `src/test/2025-07/WETC_Token_exp.sol` | `transfer`+`skim`+`sync` 使 reserve 与 balance 脱节，再 swap 获利；与 KRC 同族 | ~~候补 / hold-out~~ **已移除：NOT_VERIFIED** |
| `src/test/2025-04/YBToken_exp.sol` | `getReserves` vs `balanceOf`、`getAmount0ToReachK` 等，通过 flash+ 多次 swap 操纵 K 与报价 | ~~典型 3~~ **已移除：NOT_VERIFIED** |
| `src/test/2025-01/LAURAToken_exp.sol` | `removeLiquidityWhenKIncreases` 与 pair 的 LAURA 余额变化组合，可抽走 WETH；README：pair-balance-manipulation | 候补 / hold-out |

- **NGP Root cause**：`Trigger the sync() in _update() of NGT token`，在 swap 路径中错误地 sync，使 reserve/价格被操控。
- **KRC**：fee-on-transfer + 对 pair 的 `transfer`+`skim` 序列，典型 reserve 与 balance 不同步。
- **YBToken Root cause**：pair 的 `getReserves` 与真实 `balanceOf` 在 flash+多轮 swap 下不同步；**已移除：NOT_VERIFIED**。

**建议**：T10 选 **NGP** + **KRC**；YBToken、WETC 已移除（NOT_VERIFIED）；LAURA 作 hold-out。

---

### T11 — 缺少滑点保护 (slippage-missing)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| `src/test/2025-03/DCFToken_exp.sol` |  bonding/swap 无 `minOut` 或等价保护，flash 多池套利 | **典型 1** |
| `src/test/2025-03/Pump_exp.sol` | `buyToken(0, address(0), 0, pair)`、`exactInputSingle(amountOutMinimum: 0)` 等，多类 pump 式 token 无 minOut | **典型 2** |
| `src/test/2024-10/SASHAToken_exp.sol` | fee-on-transfer + `exactInputSingle(amountOutMinimum: 0)`，无滑点保护下抽走 WETH | **典型 3** |

- **DCFToken**：README "lack-of-slippage-protection"。
- **Pump**：README "not-slippage-protection"；多 token 通用。
- **SASHAToken**：fee-on-transfer 下 `amountOutMinimum: 0`，实际到账与 amount 假设偏差被放大，典型 T11。

---

### T12 — 首次铸币/空池 (first-deposit-empty-pool)

| 路径 | 漏洞摘要 | 选为 |
|------|----------|------|
| （待补） | `src/test` 中未见以「首次铸币/空池 share 操纵」为主的 token PoC；多为 V2 池、staking 等 | **待从外补或从 T10 的 LAURA/YB 中拆出** |

---

### 其他 / 业务逻辑（可映射或单列）

| 路径 | 漏洞摘要 | 建议 |
|------|----------|------|
| `src/test/2026-01/PRXVT_exp.sol` | `stPRXVT.claimReward`、`stake`、`earned`；README：business logic flaw | 可并作 **T05** 或单独「业务逻辑」；作 **hold-out** 较合适 |
| `src/test/2025-07/RANTToken_exp.sol` | `IERC20(RANT).transfer(RANT, huge)`：向 token 地址转实现 burn，再配合 pair swap 与 pancakeCall；逻辑偏 token 经济与回调 | 可作 **T04 候补** 或 **hold-out**（RANT 为 Token，已保留） |

---

## 二、每类 1~2 个典型的最终选取（用于设计/调参）

| 类型 | 典型 1 | 典型 2 | 说明 |
|------|--------|--------|------|
| T01 | MTToken_exp | — | 仅此一例明显 unbounded fee shares |
| T02 | — | — | 已移除：futureswap NOT_VERIFIED |
| T03 | 3913_exp | FIL314_exp | 通缩 + 核算假设 |
| T04 | MFT_exp | LABUBU_exp | transfer 内 burn/sell；LABUBU transfer 到自身钩子；P719 已移除 NOT_VERIFIED |
| T05 | LPMine_exp | — | reward 公式与时间/balance |
| T06 | CAROLProtocol_exp | Penpiexyzio_exp | 重入；Penpie 含 reward 作 hold-out |
| T07 | NORMIE_exp | TGBS_exp | fee-on-transfer 与 pair burn |
| T08 | 98Token_exp | — | 无权限的 public |
| T09 | Truebit_exp | yETH_exp | overflow；unsafe math |
| T10 | NGP_exp | KRCToken_pair_exp | sync 操纵；transfer+skim 不同步；KRC、YB 已移除 NOT_VERIFIED |
| T11 | DCFToken_exp | Pump_exp、SASHAToken_exp | 无 minOut |
| T12 | （待补） | — | 需从外或从 LAURA 等拆 |

合计 **17 个** 正样本、**4 个** hold-out（含 Token 与 非Token 如 Pair/Pool/Staking/Protocol/Swap；已移除 NOT_VERIFIED：futureswap、P719、WETC、YBToken）。

---

## 三、负样本（Negative Samples）

- **仓库内**：`src/test` 以漏洞 PoC 为主，**未见已标注「安全/加固」的 token 或 staking 合约**。
- **建议**：
  - **负样本需自建或从外部选取**，例如：
    - 正确做 `sum(percent)<=100` 的 fee 分配；
    - 用 `balanceOf(to)-balanceBefore` 处理 fee-on-transfer 的 router/pair 逻辑；
    - 带 `onlyOwner` 的 `setFee`/`setReward`、以及 `minOut` 的 swap。
  - 若暂时不做自建，可在 `benchmark_labels` 中把 **3–4 个负样本** 标为「待引入」，scanner 首版只评估正样本与 hold-out；后续再补 FP 率。

---

## 四、Hold-out 建议（仅最终评估，不参与设计/调参）

从 **与典型样本差异大、或实现复杂、或跨多类型** 的 case 中选 4–5 个：

| 路径 | 类型 | 理由 |
|------|------|------|
| `src/test/2024-09/Penpiexyzio_exp.sol` | T05+T06 | Pendle 集成、自定义 reward 合约、重入+reward 混合 |
| `src/test/2026-01/PRXVT_exp.sol` | 业务逻辑 / T05 相关 | stPRXVT、claimReward、Universal Router，与纯 reward 公式类不同 |
| `src/test/2025-01/LAURAToken_exp.sol` | T10 / T12 边缘 | `removeLiquidityWhenKIncreases`、pair 余额与 K，LAURA 为 Token |
| `src/test/2025-07/WETC_Token_exp.sol` | T10 | ~~与 KRC 同族~~ **已移除：NOT_VERIFIED** |
| `src/test/2025-07/RANTToken_exp.sol` | T04 边缘 / 业务逻辑 | `transfer(RANT, amount)` burn + pancakeCall，RANT 为 Token |

**建议 hold-out 集合**：**Penpiexyzio_exp**、**PRXVT_exp**、**LAURAToken_exp**、**RANTToken_exp**（4 个；WETC 已移除 NOT_VERIFIED）。

---

## 五、Benchmark 汇总表（供 `benchmark_candidates.csv` / `benchmark_labels.csv`）

### 正样本（按类型，每类 1~2）

| contract_path | vuln_types | root_cause_1line | has_poc | is_negative | is_holdout |
|---------------|------------|------------------|---------|-------------|------------|
| src/test/2026-01/MTToken_exp.sol | T01 | transactionFee 多比例无 sum≤100，pair 成 fee 目标 | 1 | 0 | 0 |
| src/test/2023-11/3913_exp.sol | T03 | 通缩币按 amount 核算，未用 balanceOf 差量 | 1 | 0 | 0 |
| src/test/2024-04/FIL314_exp.sol | T03 | hourBurn 通缩 + transfer 到自身当 sell，amount 假设错误 | 1 | 0 | 0 |
| src/test/2024-11/MFT_exp.sol | T04 | transfer 内对 sell 路径 burn 池子，skim+swap 抽报价币 | 1 | 0 | 0 |
| src/test/2025-01/LPMine_exp.sol | T05 | 用 pair balance 算 reward 且时间未更新，可多次 extractReward | 1 | 0 | 0 |
| src/test/2023-11/CAROLProtocol_exp.sol | T06 | sell 先转 WETH，receive 中重入协议 | 1 | 0 | 0 |
| src/test/2024-05/NORMIE_exp.sol | T07 | fee-on-transfer，协议按 amount=到账假设 | 1 | 0 | 0 |
| src/test/2024-03/TGBS_exp.sol | T07 | _burnBlock 时 transfer 在 pair 内 burn，到账≠amount | 1 | 0 | 0 |
| src/test/2025-01/98Token_exp.sol | T08 | swapTokensForTokens 等无权限，任何人可抽 token | 1 | 0 | 0 |
| src/test/2026-01/Truebit_exp.sol | T09 | totalSupply*totalSupply overflow，solveForAmount 错 | 1 | 0 | 0 |
| src/test/2025-12/yETH_exp.sol | T09 | virtual_balance/vb_prod_sum/update_rates 等 unsafe math | 1 | 0 | 0 |
| src/test/2025-09/NGP_exp.sol | T10 | NGT _update 中 sync 在 swap 路径操纵 reserve/价格 | 1 | 0 | 0 |
| src/test/2025-05/KRCToken_pair_exp.sol | T10 | fee-on-transfer+transfer+skim 使 reserve 与 balance 不同步 | 1 | 0 | 0 |
| src/test/2025-03/DCFToken_exp.sol | T11 | bonding/swap 无 minOut | 1 | 0 | 0 |
| src/test/2025-03/Pump_exp.sol | T11 | buyToken/exactInputSingle 等无 minOut | 1 | 0 | 0 |
| src/test/2024-10/SASHAToken_exp.sol | T11 | fee-on-transfer + exactInputSingle amountOutMinimum=0 | 1 | 0 | 0 |
| src/test/2024-12/LABUBU_exp.sol | T04 | transfer 到自身钩子/反射，flash 中多次调用虚增余额再 swap | 1 | 0 | 0 |

### Hold-out（is_holdout=1）

| contract_path | vuln_types | root_cause_1line | has_poc | is_negative | is_holdout |
|---------------|------------|------------------|---------|-------------|------------|
| src/test/2024-09/Penpiexyzio_exp.sol | T05,T06 | 重入+reward 操纵，Pendle 自定义 reward 合约 | 1 | 0 | 1 |
| src/test/2026-01/PRXVT_exp.sol | T05 或 业务逻辑 | stPRXVT claimReward 与转移下的业务逻辑缺陷 | 1 | 0 | 1 |
| src/test/2025-01/LAURAToken_exp.sol | T10 | removeLiquidityWhenKIncreases 与 pair 余额操纵 | 1 | 0 | 1 |
| src/test/2025-07/RANTToken_exp.sol | T04 或 业务逻辑 | transfer(RANT,amount) burn + pancakeCall 回调 | 1 | 0 | 1 |

### 负样本（待引入，is_negative=1）

| contract_path | vuln_types | root_cause_1line | has_poc | is_negative | is_holdout |
|---------------|------------|------------------|---------|-------------|------------|
| （待自建或外选） | — | 正确 fee 分配、balanceOf 差量、minOut、权限 | — | 1 | 0 |

---

## 六、Case 目录与漏洞合约源码

- 每个候选在 `benchmark/cases/` 下均有独立 case 目录（正样本 T01–T15、T17–T18，hold-out T99_1–T99_4；含 Token 与 非Token，已移除 NOT_VERIFIED：futureswap、P719、WETC、YBToken），见 `benchmark/cases/README.md`。
- `benchmark/cases/manifest.json` 列出：链、漏洞合约地址、PoC 路径。
- 漏洞合约源码需从区块浏览器拉取：在仓库根执行  
  `python3 token-flow-scanner/benchmark/scripts/fetch_contract_sources.py`（需联网）。  
  若某合约未验证或拉取失败，该 case 下会保留 `NOT_VERIFIED.txt`，内有 `#code` 链接，可手动复制后存为 `vulnerable.sol`。

## 七、PoC 运行备注

- 多数需 `vm.createSelectFork("bsc"|"mainnet"|"base", block)`，部分需 `deal` 或特定 RPC。
- 具体命令见各 `*_exp.sol` 及 `past/README.md`；例如：
  - `forge test --contracts ./src/test/2026-01/MTToken_exp.sol -vvv`
  - `forge test --contracts ./src/test/2023-11/3913_exp.sol -vvv`

---

## 八、与 PLAN 的对应

- **D4**：可直接把上表写入 `benchmark_candidates.csv` / `benchmark_labels.csv`。
- **负样本**：在 D12 之前选定「自建路径」或「外部合约路径」，再填入 `benchmark_labels`。
- **T12**：若从 LAURA 等拆出 first-deposit 逻辑或从外补一个，再追加一行；否则 T12 暂时标「待补」。
