# DeFiHackLabs Attack Vector Ranking

Generated: 2026-06-27 04:27 UTC
Total PoC cases: 689
Classification errors: 0
Count mode: `primary` (each vector tag per case)

## Ranking (descending by occurrence)

| Rank | ID | Attack Vector (EN) | 中文 | Count | % of Cases |
|------|-----|-------------------|------|-------|------------|
| 1 | AV04 | flash-loan-assisted | 闪电贷辅助攻击 | 245 | 35.6% |
| 2 | AV02 | price-oracle-manipulation | 价格预言机操纵 | 194 | 28.2% |
| 3 | AV03 | access-control | 权限控制缺失 | 56 | 8.1% |
| 4 | AV06 | arbitrary-external-call | 任意外部调用 | 36 | 5.2% |
| 5 | AV20 | liquidity-pool-manipulation | 流动性池操纵 | 33 | 4.8% |
| 6 | AV05 | business-logic-error | 业务逻辑错误 | 27 | 3.9% |
| 7 | AV10 | deflationary-fee-on-transfer | 通缩/转账费代币不兼容 | 25 | 3.6% |
| 8 | AV01 | reentrancy | 重入 | 21 | 3.0% |
| 9 | AV07 | signature-approval-abuse | 签名/授权滥用 | 14 | 2.0% |
| 10 | AV14 | uninitialized-contract | 未初始化合约 | 12 | 1.7% |
| 11 | AV13 | mev-sandwich-frontrun | MEV/三明治/抢跑 | 5 | 0.7% |
| 12 | AV15 | slippage-missing | 缺少滑点保护 | 5 | 0.7% |
| 13 | AV17 | transfer-hook-manipulation | Transfer钩子操纵 | 3 | 0.4% |
| 14 | AV12 | rug-social-engineering | Rug/密钥泄露/社工 | 3 | 0.4% |
| 15 | AV08 | arithmetic-overflow-rounding | 算术溢出与精度 | 3 | 0.4% |
| 16 | AV19 | fee-logic-error | Fee逻辑错误 | 3 | 0.4% |
| 17 | AV09 | proxy-upgrade-flaw | 代理/升级漏洞 | 2 | 0.3% |
| 18 | AV11 | bridge-cross-chain | 跨链/桥漏洞 | 2 | 0.3% |

## Top examples per vector

### AV04 — flash-loan-assisted
- `src/test/2018-10/SpankChain_exp.sol` — The exploit relies on a flash loan to manipulate the SpankChain protocol's channel creation and timeout functions.
- `src/test/2020-09/bzx_exp.sol` — The exploit relies on a flash loan to manipulate token transfers and balances.
- `src/test/2020-10/HarvestFinance_exp.sol` — The exploit relies on flash loans to manipulate token swaps and extract value from the protocol.

### AV02 — price-oracle-manipulation
- `src/test/2020-08/Opyn_exp.sol` — The attacker manipulated the price of collateral options to mint tokens at an incorrect valuation.
- `src/test/2021-02/Yearn_ydai_exp.sol` — The exploit manipulates the liquidity pool to extract tokens at an incorrect price due to imbalanced liquidity.
- `src/test/2021-04/Uranium_exp.sol` — The exploit manipulates the liquidity pool's reserves to extract funds at an incorrect price.

### AV03 — access-control
- `src/test/2020-06/Bancor_exp.sol` — The Bancor contract's 'safeTransferFrom' function is public, allowing unauthorized transfers due to missing access control.
- `src/test/2021-07/Levyathan_exp.sol` — The private keys to a wallet with minting capability were publicly available, allowing unauthorized ownership transfer.
- `src/test/2021-08/PolyNetwork_exp.sol` — The EthCrossChainManager contract lacks proper access control, allowing unauthorized users to trigger critical functions.

### AV06 — arbitrary-external-call
- `src/test/2020-11/Pickle_exp.sol` — The exploit allows for arbitrary external calls to be made, enabling the attacker to manipulate contract behavior and extract funds.
- `src/test/2021-05/RariCapital_exp.sol` — The exploit relies on an arbitrary external call to a vulnerable contract, allowing the attacker to manipulate funds.
- `src/test/2022-02/Meter_exp.sol` — The exploit relies on a user-controlled external call to manipulate token swaps, enabling theft.

### AV20 — liquidity-pool-manipulation
- `src/test/2020-06/Balancer_20200628_exp.sol` — The exploit manipulates liquidity pool balances through a series of swaps, leading to profit extraction.
- `src/test/2021-01/Sushi_Badger_Digg_exp.sol` — The exploit manipulates liquidity pools by creating a fake pair and extracting value through liquidity removal.
- `src/test/2021-05/BurgerSwap_exp.sol` — The exploit manipulates liquidity pool balances to extract value through a series of token swaps and flash loans.

### AV05 — business-logic-error
- `src/test/2020-12/Cover_exp.sol` — Flawed logic in reward claiming allows for incorrect reward calculations.
- `src/test/2021-09/Nimbus_exp.sol` — Flawed accounting logic leads to inconsistent value handling in the exploit function.
- `src/test/2021-09/NowSwap_exp.sol` — Flawed accounting logic leads to inconsistent value handling in the swap function.

### AV10 — deflationary-fee-on-transfer
- `src/test/2018-04/BEC_exp.sol` — The exploit takes advantage of a fee-on-transfer mechanism that incorrectly assumes the transfer amount equals the balance delta.
- `src/test/2022-09/DPC_exp.sol` — The exploit takes advantage of a fee-on-transfer token logic that assumes the transfer amount equals the balance delta.
- `src/test/2022-09/Shadowfi_exp.sol` — The exploit takes advantage of fee-on-transfer tokens, leading to incorrect balance calculations during swaps.

### AV01 — reentrancy
- `src/test/2021-12/Grim_exp.sol` — The exploit leverages a reentrancy vulnerability in the GrimBoostVault's depositFor function.
- `src/test/2022-03/HundredFinance_exp.sol` — The exploit leverages reentrancy through ERC667 token hooks to manipulate the contract state before updates.
- `src/test/2022-03/TreasureDAO_exp.sol` — The exploit re-enters the protocol via the onERC721Received callback before state updates occur.

### AV07 — signature-approval-abuse
- `src/test/2018-04/SmartMesh_exp.sol` — The exploit relies on signature replay to manipulate token transfers.
- `src/test/2021-07/Chainswap_exp1.sol` — The exploit relies on signature replay and validation bypass on signed messages.
- `src/test/2021-07/Chainswap_exp2.sol` — The exploit relies on signature replay to manipulate contract calls.

### AV14 — uninitialized-contract
- `src/test/2017-11/Parity_kill_exp.sol` — The contract allows an attacker to initialize and take ownership without proper access control.
- `src/test/2021-06/88mph_exp.sol` — The vulnerability arises from an unprotected init() function that allows an attacker to become the owner of the NFT contract.
- `src/test/2021-09/DaoMaker_exp.sol` — The contract's init function is unprotected, allowing an attacker to reinitialize it and gain ownership.
