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
  uint256 public lockLength;
  uint256 public amountRSRToLock;
  mapping (uint256 => Locker) public proposalIDToLocker;
  Manager public manager;


  constructor(
    IERC20 _RSR,
    uint256 _lockLength,
    uint256 _amountRSRToLock
  ) public {
    RSR = _RSR;
    lockLength = _lockLength;
    amountRSRToLock = _amountRSRToLock;
  }



  // ========================= Public + External ============================

  /// Set the lockLength.
  function setLockLength(uint256 _lockLength) external onlyOwner {
    lockLength = _lockLength;
  }

  ///
  function setAmountRSRToLock(uint256 _amountRSRToLock) external onlyOwner {
    amountRSRToLock = _amountRSRToLock;
  }

  ///
  function setManager(Manager _manager) external onlyOwner {
    manager = _manager;
  }


  function _lock() private returns (Locker) {
    // The tx will revert without this check anyway, but nice for clarity
    require(address(manager) != address(0), "manager needs to be set");

    Locker locker = new Locker(
      _msgSender(),
      now,
      RSR,
      lockLength
    );

    RSR.safeTransferFrom(
      _msgSender(),
      address(locker),
      amountRSRToLock
    );

    return locker;
  }

  function lockAndProposeSwap(
    address[] calldata tokens,
    uint256[] calldata amounts, // unit: qToken
    bool[] calldata toVault
  ) external {
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
