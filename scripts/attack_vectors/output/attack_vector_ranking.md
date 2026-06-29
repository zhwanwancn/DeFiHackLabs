# DeFiHackLabs Attack Vector Ranking

Generated: 2026-06-27 04:27 UTC
Total PoC cases: 689
Classification errors: 0
Count mode: `case` (each vector tag per case)

## Ranking (descending by occurrence)

| Rank | ID | Attack Vector (EN) | 中文 | Count | % of Cases |
|------|-----|-------------------|------|-------|------------|
| 1 | AV04 | flash-loan-assisted | 闪电贷辅助攻击 | 532 | 77.2% |
| 2 | AV05 | business-logic-error | 业务逻辑错误 | 282 | 40.9% |
| 3 | AV02 | price-oracle-manipulation | 价格预言机操纵 | 222 | 32.2% |
| 4 | AV19 | fee-logic-error | Fee逻辑错误 | 170 | 24.7% |
| 5 | AV03 | access-control | 权限控制缺失 | 94 | 13.6% |
| 6 | AV20 | liquidity-pool-manipulation | 流动性池操纵 | 89 | 12.9% |
| 7 | AV06 | arbitrary-external-call | 任意外部调用 | 87 | 12.6% |
| 8 | AV10 | deflationary-fee-on-transfer | 通缩/转账费代币不兼容 | 39 | 5.7% |
| 9 | AV01 | reentrancy | 重入 | 32 | 4.6% |
| 10 | AV15 | slippage-missing | 缺少滑点保护 | 30 | 4.4% |
| 11 | AV07 | signature-approval-abuse | 签名/授权滥用 | 29 | 4.2% |
| 12 | AV17 | transfer-hook-manipulation | Transfer钩子操纵 | 29 | 4.2% |
| 13 | AV14 | uninitialized-contract | 未初始化合约 | 13 | 1.9% |
| 14 | AV13 | mev-sandwich-frontrun | MEV/三明治/抢跑 | 8 | 1.2% |
| 15 | AV12 | rug-social-engineering | Rug/密钥泄露/社工 | 5 | 0.7% |
| 16 | AV11 | bridge-cross-chain | 跨链/桥漏洞 | 4 | 0.6% |
| 17 | AV08 | arithmetic-overflow-rounding | 算术溢出与精度 | 4 | 0.6% |
| 18 | AV09 | proxy-upgrade-flaw | 代理/升级漏洞 | 4 | 0.6% |

## Top examples per vector

### AV04 — flash-loan-assisted
- `src/test/2018-10/SpankChain_exp.sol` — The exploit relies on a flash loan to manipulate the SpankChain protocol's channel creation and timeout functions.
- `src/test/2020-09/bzx_exp.sol` — The exploit relies on a flash loan to manipulate token transfers and balances.
- `src/test/2020-10/HarvestFinance_exp.sol` — The exploit relies on flash loans to manipulate token swaps and extract value from the protocol.

### AV05 — business-logic-error
- `src/test/2020-12/Cover_exp.sol` — Flawed logic in reward claiming allows for incorrect reward calculations.
- `src/test/2021-09/Nimbus_exp.sol` — Flawed accounting logic leads to inconsistent value handling in the exploit function.
- `src/test/2021-09/NowSwap_exp.sol` — Flawed accounting logic leads to inconsistent value handling in the swap function.

### AV02 — price-oracle-manipulation
- `src/test/2020-08/Opyn_exp.sol` — The attacker manipulated the price of collateral options to mint tokens at an incorrect valuation.
- `src/test/2021-02/Yearn_ydai_exp.sol` — The exploit manipulates the liquidity pool to extract tokens at an incorrect price due to imbalanced liquidity.
- `src/test/2021-04/Uranium_exp.sol` — The exploit manipulates the liquidity pool's reserves to extract funds at an incorrect price.

### AV19 — fee-logic-error
- `src/test/2022-11/BrahTOPG_exp.sol` — The exploit takes advantage of unbounded fee percentages and missing minimum output requirements in the token swap process.
- `src/test/2024-08/YodlRouter_exp.sol` — The exploit takes advantage of unbounded fee percentages in the transferFee function, allowing excessive fees to be charged.
- `src/test/2026-01/MTToken_exp.sol` — MT token's transactionFee() allows unbounded fee percentages, leading to excessive charges during transfers.

### AV03 — access-control
- `src/test/2020-06/Bancor_exp.sol` — The Bancor contract's 'safeTransferFrom' function is public, allowing unauthorized transfers due to missing access control.
- `src/test/2021-07/Levyathan_exp.sol` — The private keys to a wallet with minting capability were publicly available, allowing unauthorized ownership transfer.
- `src/test/2021-08/PolyNetwork_exp.sol` — The EthCrossChainManager contract lacks proper access control, allowing unauthorized users to trigger critical functions.

### AV20 — liquidity-pool-manipulation
- `src/test/2020-06/Balancer_20200628_exp.sol` — The exploit manipulates liquidity pool balances through a series of swaps, leading to profit extraction.
- `src/test/2021-01/Sushi_Badger_Digg_exp.sol` — The exploit manipulates liquidity pools by creating a fake pair and extracting value through liquidity removal.
- `src/test/2021-05/BurgerSwap_exp.sol` — The exploit manipulates liquidity pool balances to extract value through a series of token swaps and flash loans.

### AV06 — arbitrary-external-call
- `src/test/2020-11/Pickle_exp.sol` — The exploit allows for arbitrary external calls to be made, enabling the attacker to manipulate contract behavior and extract funds.
- `src/test/2021-05/RariCapital_exp.sol` — The exploit relies on an arbitrary external call to a vulnerable contract, allowing the attacker to manipulate funds.
- `src/test/2022-02/Meter_exp.sol` — The exploit relies on a user-controlled external call to manipulate token swaps, enabling theft.

### AV10 — deflationary-fee-on-transfer
- `src/test/2018-04/BEC_exp.sol` — The exploit takes advantage of a fee-on-transfer mechanism that incorrectly assumes the transfer amount equals the balance delta.
- `src/test/2022-09/DPC_exp.sol` — The exploit takes advantage of a fee-on-transfer token logic that assumes the transfer amount equals the balance delta.
- `src/test/2022-09/Shadowfi_exp.sol` — The exploit takes advantage of fee-on-transfer tokens, leading to incorrect balance calculations during swaps.

### AV01 — reentrancy
- `src/test/2021-12/Grim_exp.sol` — The exploit leverages a reentrancy vulnerability in the GrimBoostVault's depositFor function.
- `src/test/2022-03/HundredFinance_exp.sol` — The exploit leverages reentrancy through ERC667 token hooks to manipulate the contract state before updates.
- `src/test/2022-03/TreasureDAO_exp.sol` — The exploit re-enters the protocol via the onERC721Received callback before state updates occur.

### AV15 — slippage-missing
- `src/test/2023-02/SwapX_exp.sol` — The exploit allows for value extraction by manipulating swaps with zero or missing minimum output parameters.
- `src/test/2023-12/TransitFinance_exp.sol` — The exploit allows for swaps with zero or missing minimum output, enabling value extraction through manipulated pools.
- `src/test/2024-06/Bazaar_exp.sol` — The exploit allows for withdrawals with zero minimum output, enabling value extraction from manipulated pools.
