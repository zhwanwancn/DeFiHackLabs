从 AI 做漏洞扫描的最佳实践分析你的计划。先查看仓库中已有的 token 类漏洞案例，便于给出具体建议。


[7 tools called]


结合 DeFiHackLabs 里的真实案例和常见 AI 安全扫描实践，下面是对你当前做法和可改进点的整理。

---

## 一、整体思路：有什么问题、什么可取

### 可取之处
- **Benchmark 先行**：有标注好的 ground truth，才能客观评估 scanner 的召回/精确率，这一点是对的。
- **聚焦 Token 合约**：通缩/税费/奖励类 ERC20 变体有相对固定的模式，很适合做成专门 scanner。
- **按 severity 分层**：从高危到低危都覆盖，和实际审计需求一致。

### 需要警惕的问题
- **“10~15 个合约”按数量来设计**：容易变成“为了凑够 15 个”而选 case，而不是按**漏洞类型**系统覆盖。
- **只有存在漏洞的合约**：如果 benchmark 里全是“有洞”的合约，没有**安全/加固**样本，模型或规则容易学会“总是报漏洞”，假阳性会很高。
- **一个合约多种漏洞**：真实里一个 token 可能同时有：fee 逻辑错 + 重入 + 访问控制弱。如果只标“有/无漏洞”，会丢失细粒度信息，也不利于按类型优化。

---

## 二、从 AI 最佳实践看的 6 个问题

### 1. 选择偏置（Selection Bias）与覆盖不全

**现象**：10~15 个若按“好找、有现成 PoC”来选，容易集中在某几类（如 deflationary + AMM、reward 计算），而漏掉：

- 单位/精度混用（如 futureswap 的 fee 单位当 bps 用）
-  unbounded 百分比/多 fee 目标且不校验 `sum(shares)<=100`（如 MTToken）
- 只和 ERC20 本身相关的：approval 前端跑、`transfer`/`transferFrom` 返回值不检查、fee-on-transfer 与 `balanceOf` 的假设不一致
- 与上下游协议的**不兼容**：通缩币 + 普通 AMM/借贷协议未用 `balanceOf` 差量

**建议**：**先定漏洞类型（taxonomy），再按类型选 1–2 个典型合约**，而不是先凑 10~15 个再归纳类型。

---

### 2. 过拟合与“benchmark 内过好、真实场景崩塌”

**现象**：若 scanner 的规则/提示/模型主要是对着这 10~15 个调出来的，很容易：
- 在这 15 个上 recall/precision 都很高；
- 对**同类型但实现方式不同**的漏洞（例如 fee 逻辑换一种写法）失效；
- 对**新型变种**（未在 benchmark 出现过的模式）漏报。

**建议**：
- Benchmark 要**分集合**：例如 10 个做“训练/提示设计/规则挖掘”，5 个做 **hold-out 测试**，且 hold-out 尽量选实现差异大、年份不同的案例；
- 或采用 **k-fold**：多次划分，确保每个 case 都当过测试集，观察方差。

---

### 3. 缺少负样本（Negative Examples）

**现象**：若 10~15 个全是“有问题”的合约，scanner 会倾向于：
- 凡是有 `takeFee`、`_tax`、`rebase`、`claimReward` 就报；
- 或凡是有复杂算术就报 overflow/rounding。

结果是：**假阳性极高**，在真实审计里不可用。

**建议**：在 10~15 个里显式加入 **3–5 个“安全/加固”样本**，例如：
- 正确实现 fee、且做 `sum<=100` 校验的通缩币；
- 正确用 `balanceOf` 差量处理 fee-on-transfer 的 pair/router；
- 规范的 reward 计算（含 rounding 安全、重入防护）。

用来专门测 **False Positive Rate**。

---

### 4. 标注粒度与多标签

**现象**：若只标“有漏洞 / 无漏洞”，会：
- 说不清是哪种漏洞，不利于按类型调优；
- 一个合约多个洞时，无法衡量“某类漏洞的召回率”。

**建议**：每个 benchmark 合约做**多标签**，例如：

```
MTToken_exp.sol:    [fee-logic-unbounded-shares, fee-target-contract-abuse, sync-skim-drain]
futureswap_exp.sol: [unit-mismatch-fee-bps]
3913Token:          [deflationary-transfer-incompatible, balance-accounting]
NORMIE:             [fee-on-transfer, launch-block-fee]
MFT:                [transfer-hook-burn-pool, skim-drain]
...
```

这样评估时可以按**每种漏洞类型**算 recall，按**每种 pattern** 调 prompt/规则。

---

### 5. Ground Truth 质量与 PoC 的作用

**现象**：若只有“人觉得这里有问题”的结论，而没有**可执行 PoC** 或**明确攻击路径**，会：
- 把设计上的“不优雅”标成漏洞，产生假阳性；
- 或把难以利用的 edge case 标成高危，导致 severity 噪音大。

**建议**：
- 每个 benchmark 漏洞尽量对应：**DeFiHackLabs 里已有 PoC**，或你自己写的、可 `forge test` 通过的 exploit；
- 在标注里写清：**Root cause 一句 + 利用条件（是否需要 flash loan、是否依赖特定 DEX/池子）**；  
这样 AI 生成报告时，可以要求“必须能对应到可验证的 root cause”，减少幻觉。

---

### 6. 可解释性与运维

**现象**：若 scanner 只输出“高危 / 中危 / 低危”或片段，而**不指出**：
- 违反了什么不变量、
- 哪条代码路径、哪类模式、

审计员难以复用，且**误报多了会直接弃用**。

**建议**：
- 对每个漏洞类型维护**简短模板**：  
  `[类型名] + [典型代码模式] + [违反的不变量/假设] + [建议的修复方向]`；
- AI 的输出格式强制包含：**类型、代码位置、根因摘要、severity**，便于和 benchmark 的标注对齐，也便于后续做规则/提示的 A/B 测试。

---

## 三、Token 漏洞类型（建议的 taxonomy）

结合 DeFiHackLabs 和 academy 资料，下面这些类型适合作为**优先覆盖**，并每种在 benchmark 中至少 1 个代表：

| 类型 | 简要说明 | 在仓库中的代表案例 |
|------|----------|--------------------|
| **fee-logic-unbounded-shares** | 多比例分配 fee 未约束 `sum<=100`，或对合约地址也收高额 fee | MTToken |
| **fee-unit-mismatch** | 金额与 bps/weight 等单位混用 | futureswap |
| **deflationary-incompatible** | 按 `amount` 而非 `balanceOf` 差量核算，与通缩/税费不兼容 | BGLD, AES, 3913Token, ZABU, SafeDollar, Balancer+STA |
| **transfer-hook-manipulation** | `transfer` 内 burn/再分配，被 AMM 的 skim/路由等利用 | MFT_exp |
| **reward-calculation-error** |  rewards 公式、舍入、`block.number`/`timestamp` 误用 | SWAPPStaking, LPMine, SorStaking, VTF, RL, DPC, SNK |
| **reentrancy** | 在 `transfer`/`receive` 回调中再次进入 sell/withdraw 等 | CAROL, Penpie |
| **fee-on-transfer-assumption** | 假设 `balanceOf` 增量为 `amount`，未用 `balanceBefore/After` | 多个 `SupportingFeeOnTransferTokens` 的误用 |
| **access-control-fee-or-reward** | 改 fee、reward 参数或抽走资金无权限/时间锁 | 多种 admin/owner 类 |
| **arithmetic-overflow-rounding** | 乘除顺序、精度截断被放大 (如 Truebit overflow) | Truebit, yETH 等 |
| **price-oracle-manipulation** | 用 AMM 现货/ reserve 做 oracle，可被 flash loan 操纵 | BGLD, AES, NGP 等 |
| **slippage-missing** | 兑换/claim 无 `minOut` 或等价保护 | DCFToken, Pump, YVToken 等 |
| **first-deposit / empty-pool** | 首次铸币或空池时的 share 计算 | 经典 first deposit 类 |

你可以先选 **8–12 个类型** 作为 v1 的必覆盖，再为每个类型选 1–2 个**有 PoC 的** benchmark，这样 10~15 个合约就变成**按类型系统覆盖**，而不是按数量随机选。

---

## 四、Benchmark 组成的建议

在“10~15 个合约”的约束下，可以按类似比例分配：

1. **按漏洞类型选 8–10 个**  
   - 每个类型 1 个，核心类型（如 fee、deflationary、reward）可 2 个；  
   - 每个都有**可运行 PoC** 和**简短 root cause**。

2. **负样本 3–4 个**  
   - 含 fee/reward 但实现正确、或明显做过加固的 token；  
   - 用于约束 False Positive。

3. **若有空间，加 1–2 个“多漏洞”合约**  
   - 用来测多标签、以及 scanner 能否列出多个问题而不是只报一个。

4. **Hold-out 5 个**  
   - 从 10~15 里固定 5 个**只用于最终评估**，不参与 prompt/规则的设计与调参，减轻过拟合。

---

## 五、和 AI 使用方式的结合

- **若用 LLM 做 scanner**：  
  - 把 taxonomy + 每个类型的**代码模式 + 错误模式**写进 system prompt，并要求输出格式包含：类型、位置、根因、severity；  
  - 用 benchmark 的**多标签 + 负样本**做 few-shot 或 RAG 示例，并做 **per-type 的 recall** 和 **负样本上的 FP 率**。

- **若用静态规则/符号 + LLM 做二次筛选**：  
  - 规则负责：`balanceOf` 用法、`sum(share)<=100`、`SupportingFeeOnTransfer` 与 `balance` 假设等；  
  - LLM 负责：结合业务语义判断是否真的可被利用、写描述。  
  - Benchmark 同样按类型评估：规则要覆盖的类型 vs 漏报；LLM 对规则候选的 FP 过滤能力。

- **评估指标**：  
  - 按**每种漏洞类型**算：Recall, Precision（或 F1）；  
  - 在**负样本**上算：False Positive 个数/率；  
  - 对多漏洞样本：是否至少命中一个、以及命中数量。

---

## 六、直接回答你的问题

- **“先筛 10~15 个做 benchmark，再让 scanner 覆盖”** 这个方向没问题，但：  
  - 若 10~15 是**按漏洞类型系统选**，并且包含**负样本 + 多标签 + 可验证 PoC**，就会好很多；  
  - 若只是“挑 10~15 个有名的、有漏洞的 token”，会有**选择偏置、过拟合、高 FP** 三个主要风险。

- **更稳妥的做法**：  
  1. 先定好 **Token 漏洞 taxonomy**（如上表，可按你需要增删）；  
  2. 按类型从 DeFiHackLabs 挑**有 PoC 的**代表，每类 1–2 个；  
  3. 专门加 **3–5 个负样本**；  
  4. 做**多标签标注 + 简短 root cause**，并固定一个 hold-out 子集；  
  5. 设计 scanner 时，**按类型**优化召回和精确率，而不是只追求“15 个全中”。

如果你愿意，我可以按你现有的 `src/test` 目录，列一版**具体的 10~15 个候选名单**（含合约路径、漏洞类型、是否有 PoC），并标出哪些适合当负样本、哪些适合当 hold-out。