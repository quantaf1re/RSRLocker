pragma solidity 0.5.7;

import "./zeppelin/token/ERC20/SafeERC20V2.sol";
import "./zeppelin/token/ERC20/IERC20.sol";
import "./zeppelin/math/SafeMathV2.sol";


contract Locker {
  using SafeERC20V2 for IERC20;
  using SafeMathV2 for uint256;

  address public lockerFactory;
  address payable public proposer;
  uint256 public startTime;
  IERC20 public RSR;
  uint256 public lockLength;

  // events

  constructor(
    address payable _proposer,
    uint256 _startTime,
    IERC20 _RSR,
    uint256 _lockLength
  ) public {
    lockerFactory = msg.sender;
    proposer = _proposer;
    startTime = _startTime;
    RSR = _RSR;
    lockLength = _lockLength;
  }

  function withdraw() external {
    // Don't need to check if proposer is calling since the tokens
    // will only ever go to the proposer anyway
    require(
      now > startTime.add(lockLength) ||
      msg.sender == address(lockerFactory),
      "not enough time has passed"
    );

    // Could just withdraw a constant amount, which is the only amount that
    // 'should' be withdrawn, but someone might've sent extra tokens here by
    // mistake and the amount can change through governance
    uint256 bal = RSR.balanceOf(address(this));
    RSR.safeTransfer(proposer, bal);
    selfdestruct(proposer);
  }

}
