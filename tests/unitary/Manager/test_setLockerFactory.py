from consts import *
from brownie import a, reverts
from brownie.test import given, strategy


# Tests that the setters set their values correctly and fire events correctly
@given(new_addr=strategy("address", exclude=ZERO_ADDRESS))
def test_setLockerFactory(a, ics, new_addr):
    old_addr = ics.manager.lockerFactory()
    tx = ics.manager.setLockerFactory(new_addr, {"from": a[0]})

    assert ics.manager.lockerFactory() == new_addr
    assert len(tx.events) == 1
    assert tx.events.count("LockerFactoryChanged") == 1
    assert tx.events["LockerFactoryChanged"][0]["oldFactory"] == old_addr
    assert tx.events["LockerFactoryChanged"][0]["newFactory"] == new_addr


def test_setLockerFactory_revert_zero_address(a, ics):
    with reverts("invalid address"):
        ics.manager.setLockerFactory(ZERO_ADDRESS, {"from": a[0]})


# This is outside of the scope really since `onlyOwner` should work, but just
# to be safe...
@given(
    new_addr=strategy("address", exclude=ZERO_ADDRESS),
    signer=strategy("address")
)
def test_setLockerFactory_revert_signer(a, ics, new_addr, signer):
    if signer != a[0]:
        with reverts("caller is not owner"):
            ics.manager.setLockerFactory(ZERO_ADDRESS, {"from": signer})
