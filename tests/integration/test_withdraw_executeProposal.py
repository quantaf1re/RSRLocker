from consts import *
from brownie import a, reverts, chain, Basket, SwapProposal, WeightProposal
from brownie.test import given, strategy


# A proposal should be able to be executed even if the 30d have passed and the
# funds have already been withdrawn


# Helper fcn
def withdraw_executeProposal(a, ics, locker, proposal_start_state):
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
    original_basket = Basket.at(ics.manager.trustedBasket())

    if proposal_start_state == CREATED:
        ics.manager.acceptProposal(proposal_id, {"from": a.at(ics.manager.operator())})
        assert proposal.state() == STATE_TO_NUM[ACCEPTED]
        chain.sleep(SECONDS_24H+1)

    ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})

    assert original_basket.address != Basket.at(ics.manager.trustedBasket()).address
    assert proposal.state() == STATE_TO_NUM[COMPLETED]


# Tests that a withdrawal can happen BEFORE the proposal is accepted and executed
@given(
    withdraw_delay=strategy(
        "uint256",
        min_value=INITIAL_PROPOSAL_LOCK_TIME+1,
        max_value=SECONDS_1Y
    )
)
def test_withdraw_acceptProposal_executeProposal(a, ics, lockerSwap, lockerWeights, withdraw_delay):
    chain.sleep(withdraw_delay)
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        withdraw_executeProposal(a, ics, locker, CREATED)


# Tests that a withdrawal can happen AFTER the proposal is accepted, THEN
# executed last
@given(
    withdraw_delay=strategy(
        "uint256",
        min_value=INITIAL_PROPOSAL_LOCK_TIME+1,
        max_value=SECONDS_1Y
    )
)
def test_acceptProposal_withdraw_executeProposal(a, ics, lockerSwapAccepted, lockerWeightsAccepted, withdraw_delay):
    chain.sleep(withdraw_delay)
    for locker in [ics.lockerSwap, ics.lockerWeights]:
        withdraw_executeProposal(a, ics, locker, ACCEPTED)
