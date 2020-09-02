import consts
import brownie as br
from brownie.test import given, strategy

# Initial values in constructor

def test_rsr_address(accounts, ics):
    assert ics.locker_factory.RSR() == ics.rsr.address


def test_initial_lockLength(accounts, ics):
    assert ics.locker_factory.lockTime() == consts.INITIAL_PROPOSAL_LOCK_TIME


def test_initial_RSRAmountToLock(accounts, ics):
    assert ics.locker_factory.RSRAmountToLock() == consts.INITIAL_RSR_AMOUNT_TO_LOCK


def test_manager_address(accounts, ics):
    assert ics.locker_factory.manager() == ics.manager.address


# -----Setters-----

# setRSR

@given(new_RSR_addr=strategy("address", exclude=consts.ZERO_ADDRESS))
def test_setRSR(accounts, ics, new_RSR_addr):
    ics.locker_factory.setRSR(new_RSR_addr, {"from": accounts[0]})
    assert ics.locker_factory.RSR() == new_RSR_addr


def  test_setRSR_revert(accounts, ics):
    with br.reverts("invalid address"):
        ics.locker_factory.setRSR(consts.ZERO_ADDRESS, {"from": accounts[0]})


# ||||||||||||||||||||||| this should work but doesn't? |||||||||||||||||||||||
# @given(
#     from_addr=strategy("address", exclude=br.accounts[0]),
#     new_RSR_addr=strategy("address", exclude=consts.ZERO_ADDRESS)
# )
# def test_setRSR_revert_from(accounts, ics, from_addr, new_RSR_addr):
#     with br.reverts():
#         ics.locker_factory.setRSR(new_RSR_addr, {"from": from_addr})


# setLockTime

@given(lock_time=strategy("uint256", exclude=0))
def test_setLockTime(accounts, ics, lock_time):
    ics.locker_factory.setLockTime(lock_time, {"from": accounts[0]})
    assert ics.locker_factory.lockTime() == lock_time


def test_setLockTime_revert(accounts, ics):
    with br.reverts("invalid time"):
        ics.locker_factory.setLockTime(0, {"from": accounts[0]})


# setRSRAmountToLock

@given(amount=strategy("uint256", exclude=0))
def test_setRSRAmountToLock(accounts, ics, amount):
    ics.locker_factory.setRSRAmountToLock(amount, {"from": accounts[0]})
    assert ics.locker_factory.RSRAmountToLock() == amount


def test_setRSRAmountToLock_revert(accounts, ics):
    with br.reverts("invalid amount"):
        ics.locker_factory.setRSRAmountToLock(0, {"from": accounts[0]})


# setManager

@given(new_RSR_addr=strategy("address", exclude=consts.ZERO_ADDRESS))
def test_setManager(accounts, ics, new_RSR_addr):
    ics.locker_factory.setManager(new_RSR_addr, {"from": accounts[0]})
    assert ics.locker_factory.manager() == new_RSR_addr


def  test_setManager_revert(accounts, ics):
    with br.reverts("invalid address"):
        ics.locker_factory.setManager(consts.ZERO_ADDRESS, {"from": accounts[0]})
