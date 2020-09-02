pragma solidity 0.5.7;

import "./Locker.sol";
import "./ownership/OwnableV2.sol";
import "./zeppelin/token/ERC20/IERC20.sol";
import "./zeppelin/math/SafeMathV2.sol";
import "./Manager.sol";


contract LockerFactory is OwnableV2 {
  using SafeERC20V2 for IERC20;
  using SafeMathV2 for uint256;

  IERC20 public RSR;
  uint256 public lockTime;
  uint256 public RSRAmountToLock;
  Manager public manager;
  mapping (uint256 => Locker) public proposalIDToLocker;

  // TODO: add events
  // TODO: format comments
  // add tests for things that should revert
  // add comments on units to mirror `manager`


  constructor(
    IERC20 _RSR,
    uint256 _lockTime,
    uint256 _RSRAmountToLock
  ) public {
    RSR = _RSR;
    lockTime = _lockTime;
    RSRAmountToLock = _RSRAmountToLock;
  }


  // ========================= Public + External ============================
  ///
  function setRSR(IERC20 _RSR) external onlyOwner {
    require(address(_RSR) != address(0), "invalid address");
    RSR = _RSR;
  }

  /// Set the lockTime.
  function setLockTime(uint256 _lockTime) external onlyOwner {
    require(_lockTime != 0, "invalid time");
    lockTime = _lockTime;
  }

  ///
  function setRSRAmountToLock(uint256 _RSRAmountToLock) external onlyOwner {
    require(_RSRAmountToLock != 0, "invalid amount");
    RSRAmountToLock = _RSRAmountToLock;
  }

  ///
  function setManager(Manager _manager) external onlyOwner {
    require(address(_manager) != address(0), "invalid address");
    manager = _manager;
  }


  function _lock() private returns (Locker) {
    // The tx will revert without this check anyway, but nice for clarity
    require(address(manager) != address(0), "manager needs to be set");

    Locker locker = new Locker(
      _msgSender(),
      now,
      RSR,
      lockTime
    );

    RSR.safeTransferFrom(
      _msgSender(),
      address(locker),
      RSRAmountToLock
    );

    return locker;
  }

  function lockAndProposeSwap(
    address[] calldata tokens,
    uint256[] calldata amounts, // unit: qToken
    bool[] calldata toVault
  ) external {
    // No need to repeat the same require statements that are in `manager`
    Locker locker = _lock();

    uint256 proposalID = manager.proposeSwap(
      tokens,
      amounts,
      toVault,
      _msgSender()
    );

    proposalIDToLocker[proposalID] = locker;
  }

  function lockAndProposeWeights(
    address[] calldata tokens,
    uint256[] calldata weights
  ) external {
    // No need to repeat the same require statements that are in `manager`
    Locker locker = _lock();

    uint256 proposalID = manager.proposeWeights(
      tokens,
      weights,
      _msgSender()
    );

    proposalIDToLocker[proposalID] = locker;
  }


  function cancelAndUnlock(uint256 proposalID) external {
    require(
      _msgSender() == proposalIDToLocker[proposalID].proposer() ||
      _msgSender() == manager.owner() ||
      _msgSender() == manager.operator(),
      "cannot cancel"
    );

    manager.cancelProposal(proposalID);
    proposalIDToLocker[proposalID].withdraw();
  }






















}
