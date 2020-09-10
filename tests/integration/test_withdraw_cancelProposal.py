from consts import *
from brownie import a, reverts, chain, SwapProposal, WeightProposal
from brownie.test import given, strategy


# A proposer needs to be able to cancel a proposal even after the locking
# period has finished and the tokens have already been withdrawn


# Helper fcn
def withdraw_cancelProposal(a, ics, locker, proposal_start_state):
    proposal_id = locker.proposalID()
    if proposal_id == 0:
        proposal = SwapProposal.at(ics.manager.trustedProposals(0))
    else:
        proposal = WeightProposal.at(ics.manager.trustedProposals(1))
    assert proposal.state() == STATE_TO_NUM[proposal_start_state]

    proposer = a.at(locker.proposer())
    start_bal = ics.rsr.balanceOf(proposer)

    locker.withdraw({"from": proposer})

    assert ics.rsr.balanceOf(locker.address) == 0
    bal_after_withdraw = ics.rsr.balanceOf(proposer)
    assert bal_after_withdraw == start_bal + INITIAL_RSR_AMOUNT_TO_LOCK
    assert ics.locker_factory.proposalIDToLocker(proposal_id) == locker.address
    assert ics.locker_factory.lockerAddrToProposalID(locker.address) == proposal_id
    assert proposal.state() == STATE_TO_NUM[proposal_start_state]

    ics.locker_factory.cancelAndUnlock(proposal_id, {"from": proposer})

    assert ics.rsr.balanceOf(locker.address) == 0
    assert ics.rsr.balanceOf(proposer) == bal_after_withdraw
    assert proposal.state() == STATE_TO_NUM[CANCELLED]


# Tests that cancelling a `Created` proposal works after withdrawing
@given(
    withdraw_delay=strategy(
        "uint256",
        min_value=INITIAL_PROPOSAL_LOCK_TIME+1,
        max_value=SECONDS_1Y
    )
)
def test_withdraw_cancelProposal(a, ics, lockerSwap, lockerWeights, withdraw_delay):
    chain.sleep(withdraw_delay)
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        withdraw_cancelProposal(a, ics, locker, CREATED)


# Tests that cancelling an `Accepted` proposal works after withdrawing
@given(
    withdraw_delay=strategy(
        "uint256",
        min_value=INITIAL_PROPOSAL_LOCK_TIME+1,
        max_value=SECONDS_1Y
    )
)
def test_acceptProposal_withdraw_cancelProposal(a, ics, lockerSwapAccepted, lockerWeightsAccepted, withdraw_delay):
    chain.sleep(withdraw_delay)
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        withdraw_cancelProposal(a, ics, locker, ACCEPTED)
