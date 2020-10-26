pragma solidity 0.5.7;

import "./zeppelin/token/ERC20/SafeERC20V2.sol";
import "./zeppelin/token/ERC20/IERC20.sol";
import "./zeppelin/math/SafeMathV2.sol";


contract Locker {
  using SafeERC20V2 for IERC20;
  using SafeMathV2 for uint256;


  uint256 public proposalID;
  address public lockerFactory;
  address public proposer;
  uint256 public startTime;
  // Needs a separate copy - if RSR is changed in the factory, we don't
  // want it to be changed here
  IERC20 public RSR;
  uint256 public lockLength;

  // events

  constructor(
    uint256 _proposalID,
    address _proposer,
    IERC20 _RSR,
    uint256 _lockLength
  ) public {
    proposalID = _proposalID;
    lockerFactory = msg.sender;
    proposer = _proposer;
    startTime = now;
    RSR = _RSR;
    lockLength = _lockLength;
  }

  // It would be nice to add the ability to input a token address incase people
  // send other tokens to this contract but that would introduce more complexity
  // and edge cases. It's simpler and more secure to enforce the atomicity of
  // withdrawing a set token and self-destructing
  function withdraw() external {
    // Don't need to check if proposer is calling since the tokens
    // will only ever go to the proposer anyway
    require(
      now > startTime.add(lockLength) ||
      msg.sender == address(lockerFactory),
      "too early or wrong signer"
    );

    // Could just withdraw a constant amount, which is the only amount that
    // 'should' be withdrawn, but someone might've sent extra tokens here by
    // mistake and the amount can change through governance. It also simplifies
    // handling the case of cancelling a proposal after a withdrawal
    uint256 bal = RSR.balanceOf(address(this));
    RSR.safeTransfer(proposer, bal);
  }
}
