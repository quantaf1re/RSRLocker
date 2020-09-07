import consts
from brownie import a, reverts, chain
from brownie.test import given, strategy


# Test withdrawals before any other things happen, like the proposal being
# accepted


# max_value == 1 year, brownie throws an error when delay is too large
@given(delay=strategy(
    "uint256",
    min_value=consts.INITIAL_PROPOSAL_LOCK_TIME+1,
    max_value=consts.SECONDS_1Y
))
def test_withdraw(a, ics, lockerSwap, lockerWeights, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        proposer = a.at(locker.proposer())
        start_bal = ics.rsr.balanceOf(proposer)
        locker.withdraw({"from": proposer})

        assert ics.rsr.balanceOf(proposer) == start_bal + consts.INITIAL_RSR_AMOUNT_TO_LOCK
        assert ics.rsr.balanceOf(locker.address) == 0


# Should revert if not enough time (30d) has passed
@given(delay=strategy("uint256", max_value=consts.INITIAL_PROPOSAL_LOCK_TIME))
def test_withdraw_revert_time(a, ics, lockerSwap, lockerWeights, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        with reverts("too early or wrong signer"):
            locker.withdraw({"from": a.at(locker.proposer())})


# If not enough time has passed, the only address that should be able to call
# withdraw is `lockerFactory`
@given(signer=strategy("address"))
def test_withdraw_revert_signer(a, ics, lockerSwap, lockerWeights, signer):
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        with reverts("too early or wrong signer"):
            locker.withdraw({"from": signer})
