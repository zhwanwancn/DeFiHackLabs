# Token 漏洞分类（Taxonomy）

> 初稿，供 D1–D2 修订。定稿后用于 Benchmark 标注与 Scanner 设计。

## 分类表

| ID | 中文名 | 英文名 | 定义摘要 | 典型代码特征 | 参考案例（DeFiHackLabs） |
|----|--------|--------|----------|--------------|--------------------------|
| T01 | fee 比例无界 | fee-logic-unbounded-shares | 多比例分配 fee 未约束 sum≤100，或对合约地址也收高额 fee，导致转出远多于 amount | 多个 `mul(amount, percent).div(100)` 且无 `sum(percent)<=100`；fee 目标含 pair 等合约 | MTToken |
| T02 | fee 单位混用 | fee-unit-mismatch | 金额与 bps/weight/份数等单位混用，下游按错误单位解释 | 一处按 token 数量算“费用”，另一处当 bps 或权重使用 | futureswap |
| T03 | 通缩/税费不兼容 | deflationary-incompatible | 按 `amount` 核算而实际到账为 `balanceOf` 差量，与通缩/税费不兼容 | 使用 `amount` 或 `balanceOf(to)` 代替 `balanceOf(to)-balanceBefore` | BGLD, AES, 3913Token, ZABU, SafeDollar |
| T04 | transfer 钩子操纵 | transfer-hook-manipulation | transfer 内 burn/再分配，被 AMM 的 skim/路由等利用 | 在 `_transfer` 内 burn、分给多地址、或 callback；pair 成 recipient | MFT |
| T05 | 奖励计算错误 | reward-calculation-error | reward 公式、舍入、`block.number`/`timestamp` 误用导致多领或少发 | `reward += amount * (block.number - last) * rate` 类；除序不当；精度截断 | SWAPPStaking, LPMine, SorStaking, VTF, RL, DPC, SNK |
| T06 | 重入 | reentrancy | 在 `transfer`/`receive` 等回调中再次进入 sell/withdraw/claim | 先 external call 再改 state；`receive`/fallback 中调协议 | CAROL, Penpie |
| T07 | fee-on-transfer 假设错误 | fee-on-transfer-assumption | 假设 `balanceOf` 增量为 `amount`，未用 balanceBefore/After 差量 | `getAmountOut(amountIn)` 用 amountIn 而非 `balanceOf(pair)-reserve` | 多处 SupportingFeeOnTransferTokens 误用 |
| T08 | 权限与敏感参数 | access-control-fee-or-reward | 修改 fee、reward 参数或抽走资金无权限/时间锁 | `setFee`/`setReward` 无 `onlyOwner` 或 `onlyRole`；提款无 delay | 多种 admin/owner 案例 |
| T09 | 算术溢出与舍入 | arithmetic-overflow-rounding | 乘除顺序、精度截断被放大 | 大数乘再除、`/ 1e18` 顺序不当；`mulDiv` 截断 | Truebit, yETH |
| T10 | 价格预言机操纵 | price-oracle-manipulation | 用 AMM 现货/reserve 做 oracle，可被 flash loan 操纵 | `getReserves()`/`balanceOf(pool)` 直接作价格或 share 计算 | BGLD, AES, NGP |
| T11 | 缺少滑点保护 | slippage-missing | 兑换/claim 无 minOut 或等价保护 | `swap(amountIn, 0, ...)`；`withdraw(amount)` 无 `minOut` | DCFToken, Pump, YVToken |
| T12 | 首次铸币/空池 | first-deposit-empty-pool | 首次铸币或空池时 share 计算可被操纵 | `totalSupply==0` 时 `shares = amount` 或类似，未防 1 wei 攻击 | 经典 first deposit |

## 使用说明

- **Scanner**：按 `ID` 或 `英文名` 输出，便于与 `benchmark_labels.csv` 的 `vuln_types` 对齐。
- **增删**：D2 定稿时合并重叠、补缺；若某类暂无 benchmark，可标「待补」。
- **Severity 建议**：T01–T04、T06、T10 常作高危；T05、T07–T09 视利用条件做中危；T11–T12 常中低危。
