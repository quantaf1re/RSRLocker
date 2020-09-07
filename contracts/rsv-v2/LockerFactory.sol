pragma solidity 0.5.7;

import "./Locker.sol";
import "./ownership/OwnableV2.sol";
import "./zeppelin/token/ERC20/IERC20.sol";
import "./zeppelin/math/SafeMathV2.sol";
import "./Manager.sol";


/**
 * All creations and cancellations of propsals are routed through LockerFactory.
 * This simplifies and reduces edge cases as opposed to being able to create/cancel
 * independently of LockerFactory, therefore reducing attack surface and making
 * it easier to reason about/test. Manager never needs to check whether the
 * proposer has locked up RSR because LockerFactory enforces this, therefore
 * the changes made to Manager are minimised.
 *
*/

contract LockerFactory is OwnableV2 {
  using SafeERC20V2 for IERC20;
  using SafeMathV2 for uint256;

  IERC20 public RSR;
  uint256 public lockTime;
  uint256 public RSRAmountToLock;
  Manager public manager;
  mapping (uint256 => Locker) public proposalIDToLocker;
  mapping (address => uint256) public lockerAddrToProposalID;

  // TODO: add events
  // TODO: format comments
  // add tests for things that should revert
  // add comments on units to mirror `manager`
  // turn external to public in Locker

  // Setter events
  event RSRChanged(IERC20 indexed oldAddr, IERC20 indexed newAddr);
  event LockTimeChanged(uint256 indexed oldVal, uint256 indexed newVal);
  event RSRAmountToLockChanged(uint256 indexed oldVal, uint256 indexed newVal);
  event ManagerChanged(Manager indexed oldAddr, Manager indexed newAddr);


  // locking event
   /**
   * Somewhat redundant because of the ERC20 Transfer event that should also
   * fire, but it'll make it a bit easier to filter for only locking-relevant
   * events
   */
  event Locked(uint256 indexed amount, address indexed lockerAddr);


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

  /// set the RSR address
  function setRSR(IERC20 _RSR) external onlyOwner {
    require(address(_RSR) != address(0), "invalid address");
    emit RSRChanged(RSR, _RSR);
    RSR = _RSR;
  }

  /// Set the time to lock up RSR for when creating a new Locker/Proposal
  /// _lockTime unit: seconds
  function setLockTime(uint256 _lockTime) external onlyOwner {
    require(_lockTime != 0, "invalid time");
    emit LockTimeChanged(lockTime, _lockTime);
    lockTime = _lockTime;
  }

  /// Set the amount of RSR to lock up when creating a new Locker/Proposal
  /// _RSRAmountToLock unit: qRSR
  function setRSRAmountToLock(uint256 _RSRAmountToLock) external onlyOwner {
    require(_RSRAmountToLock != 0, "invalid amount");
    emit RSRAmountToLockChanged(RSRAmountToLock, _RSRAmountToLock);
    RSRAmountToLock = _RSRAmountToLock;
  }

  /// Set the Manager to route proposal creations/cancellations through.
  /// Needs to be called atleast once because LockerFactory will be deployed
  /// before Manager is.
  function setManager(Manager _manager) external onlyOwner {
    require(address(_manager) != address(0), "invalid address");
    emit ManagerChanged(manager, _manager);
    manager = _manager;
  }

  /// Warning: need to approve `RSRAmountToLock` of RSR to this factory.
  /// Creates a new SwapProposal via proposeSwap, then creates a new Locker
  /// and transfers the proposer's RSR to it.
  /// Returns the Locker that was just created.
  function lockAndProposeSwap(
    address[] calldata tokens,
    uint256[] calldata amounts, // unit: qToken
    bool[] calldata toVault
  ) external returns(Locker) {
    // No need to repeat the same require statements that are in `manager`
    uint256 proposalID = manager.proposeSwap(
      tokens,
      amounts,
      toVault,
      _msgSender()
    );

    return lockAndRegister(proposalID);
  }

  /// Warning: need to approve `RSRAmountToLock` of RSR to this factory.
  /// Creates a new WeightProposal via proposeWeights, then creates a new Locker
  /// and transfers the proposer's RSR to it.
  /// Returns the Locker that was just created.
  function lockAndProposeWeights(
    address[] calldata tokens,
    uint256[] calldata weights
  ) external returns(Locker) {
    // No need to repeat the same require statements that are in `manager`
    uint256 proposalID = manager.proposeWeights(
      tokens,
      weights,
      _msgSender()
    );

    return lockAndRegister(proposalID);
  }

  /// Cancels a proposal that hasn't already been executed and withdraws
  /// the locked up RSR to the proposer. Can be called even if the RSR has
  /// already been withdrawn.
  function cancelAndUnlock(uint256 proposalID) external {
    // The tx will revert without this check anyway, but nice for clarity
    require(address(manager) != address(0), "manager needs to be set");
    require(
      _msgSender() == proposalIDToLocker[proposalID].proposer() ||
      _msgSender() == manager.owner() ||
      _msgSender() == manager.operator(),
      "wrong signer"
    );

    manager.cancelProposal(proposalID);
    Locker locker = proposalIDToLocker[proposalID];
    locker.withdraw();
    // Clean up. Maybe these shouldn't be deleted for records? Debatable.
    delete proposalIDToLocker[proposalID];
    delete lockerAddrToProposalID[address(locker)];
  }


  // ========================= Private ============================

  /// Creates a new Locker and sends the proposer's RSR to it
  function _lock(uint256 proposalID) private returns (Locker) {
    // The tx will revert without this check anyway, but nice for clarity
    require(address(manager) != address(0), "manager needs to be set");

    Locker locker = new Locker(
      proposalID,
      _msgSender(),
      RSR,
      lockTime
    );

    RSR.safeTransferFrom(
      _msgSender(),
      address(locker),
      RSRAmountToLock
    );

    emit Locked(RSRAmountToLock, address(locker));

    return locker;
  }

  /// Calls _lock and registers the locker & proposalID
  function lockAndRegister(uint256 proposalID) private returns(Locker) {
      Locker locker = _lock(proposalID);
      proposalIDToLocker[proposalID] = locker;
      lockerAddrToProposalID[address(locker)] = proposalID;

      return locker;
  }
}
