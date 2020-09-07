import consts
from brownie import a, reverts, chain
from brownie.test import given, strategy
from cancelAndUnlock_fn import cancelAndUnlock


# Test that a proposal which has been accepted can be cancelled and the funds
# returned


# Can't put these 3 in the same function because the state needs to reset after each
# Can't put the for loop in cancelAndUnlock since proposer might change in
# test_acceptProposal_cancelAndUnlock_as_proposer
def test_acceptProposal_cancelAndUnlock_as_owner(a, ics, lockerSwapAccepted, lockerWeightsAccepted):
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        cancelAndUnlock(a, ics, locker, ics.manager.operator(), "Accepted")


def test_acceptProposal_cancelAndUnlock_as_operator(a, ics, lockerSwapAccepted, lockerWeightsAccepted):
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        cancelAndUnlock(a, ics, locker, ics.manager.owner(), "Accepted")


def test_acceptProposal_cancelAndUnlock_as_proposer(a, ics, lockerSwapAccepted, lockerWeightsAccepted):
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        cancelAndUnlock(a, ics, locker, locker.proposer(), "Accepted")


# Cancelling should revert for all callers except proposer, owner, and operator
# For some reason the below line fails with `IndexError: list index out of range`,
# bug in brownie?
# @given(signer=strategy("address", exclude=a[1]))
def test_cancelAndUnlock_revert_signer(a, ics, lockerSwapAccepted, lockerWeightsAccepted):
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        # Because we can't use @given here for some reason. Actual length 10
        some_accounts = a[:consts.MAX_NUM_TEST_REPS]
        accounts_to_exclude = [ics.manager.owner(), ics.manager.operator(), locker.proposer()]
        for signer in [addr for addr in some_accounts if addr not in accounts_to_exclude]:
            with reverts("wrong signer"):
                ics.locker_factory.cancelAndUnlock(locker.proposalID(), {"from": a.at(signer)})
