import consts
from brownie import a, reverts
from brownie.test import given, strategy


# Tests that the setters set their values correctly and fire events correctly

# setRSR

@given(new_RSR_addr=strategy("address", exclude=consts.ZERO_ADDRESS))
def test_setRSR(a, ics, new_RSR_addr):
    old_RSR_addr = ics.locker_factory.RSR()
    tx = ics.locker_factory.setRSR(new_RSR_addr, {"from": a[0]})

    assert ics.locker_factory.RSR() == new_RSR_addr
    assert len(tx.events) == 1
    assert tx.events.count("RSRChanged") == 1
    assert tx.events["RSRChanged"][0]["oldAddr"] == old_RSR_addr
    assert tx.events["RSRChanged"][0]["newAddr"] == new_RSR_addr


def test_setRSR_revert(a, ics):
    with reverts("invalid address"):
        ics.locker_factory.setRSR(consts.ZERO_ADDRESS, {"from": a[0]})


# setLockTime

@given(new_lock_time=strategy("uint256", exclude=0))
def test_setLockTime(a, ics, new_lock_time):
    old_lock_time = ics.locker_factory.lockTime()
    tx = ics.locker_factory.setLockTime(new_lock_time, {"from": a[0]})

    assert ics.locker_factory.lockTime() == new_lock_time
    assert len(tx.events) == 1
    assert tx.events.count("LockTimeChanged") == 1
    assert tx.events["LockTimeChanged"][0]["oldVal"] == old_lock_time
    assert tx.events["LockTimeChanged"][0]["newVal"] == new_lock_time


def test_setLockTime_revert(a, ics):
    with reverts("invalid time"):
        ics.locker_factory.setLockTime(0, {"from": a[0]})


# setRSRAmountToLock

@given(new_RSR_amount=strategy("uint256", exclude=0))
def test_setRSRAmountToLock(a, ics, new_RSR_amount):
    old_RSR_amount = ics.locker_factory.RSRAmountToLock()
    tx = ics.locker_factory.setRSRAmountToLock(new_RSR_amount, {"from": a[0]})

    assert ics.locker_factory.RSRAmountToLock() == new_RSR_amount
    assert len(tx.events) == 1
    assert tx.events.count("RSRAmountToLockChanged") == 1
    assert tx.events["RSRAmountToLockChanged"][0]["oldVal"] == old_RSR_amount
    assert tx.events["RSRAmountToLockChanged"][0]["newVal"] == new_RSR_amount


def test_setRSRAmountToLock_revert(a, ics):
    with reverts("invalid amount"):
        ics.locker_factory.setRSRAmountToLock(0, {"from": a[0]})


# setManager

@given(new_manager_addr=strategy("address", exclude=consts.ZERO_ADDRESS))
def test_setManager(a, ics, new_manager_addr):
    old_manager_addr = ics.locker_factory.manager()
    tx = ics.locker_factory.setManager(new_manager_addr, {"from": a[0]})

    assert ics.locker_factory.manager() == new_manager_addr
    assert len(tx.events) == 1
    assert tx.events.count("ManagerChanged") == 1
    assert tx.events["ManagerChanged"][0]["oldAddr"] == old_manager_addr
    assert tx.events["ManagerChanged"][0]["newAddr"] == new_manager_addr


def test_setManager_revert(a, ics):
    with reverts("invalid address"):
        ics.locker_factory.setManager(consts.ZERO_ADDRESS, {"from": a[0]})


# ||||||||||||||||||||||| this should work but doesn't? |||||||||||||||||||||||
# @given(
#     from_addr=strategy("address", exclude=a[0]),
#     new_RSR_addr=strategy("address", exclude=consts.ZERO_ADDRESS)
# )
# def test_setRSR_revert_from(a, ics, from_addr, new_RSR_addr):
#     with reverts():
#         ics.locker_factory.setRSR(new_RSR_addr, {"from": from_addr})
