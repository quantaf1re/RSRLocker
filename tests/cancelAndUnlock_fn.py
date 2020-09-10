from consts import *
from brownie import SwapProposal, WeightProposal


# Checks that `cancelAndUnlock` results in the correct changes to RSR balances
# and state of the proposal.
# WARNING: CAN ONLY BE USED BEFORE A WITHDRAWAL
def cancelAndUnlock(a, ics, locker, signer, state_at_start):
    # These are the same when signer == proposer obviously
    proposer = locker.proposer()
    start_bal_signer = ics.rsr.balanceOf(signer)
    start_bal_proposer = ics.rsr.balanceOf(proposer)
    proposal_id = locker.proposalID()

    if proposal_id == 0:
        proposal = SwapProposal.at(ics.manager.trustedProposals(0))
    else:
        proposal = WeightProposal.at(ics.manager.trustedProposals(1))
    assert proposal.state() == STATE_TO_NUM[state_at_start]


    ics.locker_factory.cancelAndUnlock(proposal_id, {"from": a.at(signer)})

    if signer == proposer:
        assert ics.rsr.balanceOf(proposer) == start_bal_proposer + INITIAL_RSR_AMOUNT_TO_LOCK
    else:
        assert ics.rsr.balanceOf(proposer) == start_bal_proposer + INITIAL_RSR_AMOUNT_TO_LOCK
        assert ics.rsr.balanceOf(signer) == start_bal_signer
    assert ics.rsr.balanceOf(locker.address) == 0
    assert proposal.state() == STATE_TO_NUM[CANCELLED]
