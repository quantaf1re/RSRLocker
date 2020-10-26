from consts import *
from brownie import a, reverts


# Initial values in constructor
def test_initial_locker_factory(a, ics):
    assert ics.locker_factory.RSR() == ics.rsr.address
    assert ics.locker_factory.lockTime() == INITIAL_PROPOSAL_LOCK_TIME
    assert ics.locker_factory.RSRAmountToLock() == INITIAL_RSR_AMOUNT_TO_LOCK
    assert ics.locker_factory.manager() == ics.manager.address
    assert ics.locker_factory.proposalIDToLocker(0) == ZERO_ADDRESS
