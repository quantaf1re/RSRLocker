import consts
from brownie import accounts, reverts, chain, SwapProposal, WeightProposal
from brownie.test import given, strategy


# The following test(s) apply to `Locker`s created through both lockAndProposeSwap
# and lockAndProposeWeights

# Initial values from instantiation
def test__initial_locker(a, ics, lockerSwap, lockerWeights):
    # Test events
    for tx in [lockerSwap, lockerWeights]:
        assert len(tx.events) == 8
        assert tx.events.count("Locked") == 1
        assert tx.events["Locked"][0]["amount"] == consts.INITIAL_RSR_AMOUNT_TO_LOCK

    assert lockerSwap.events["Locked"][0]["lockerAddr"] == ics.lockerSwap.address
    assert lockerWeights.events["Locked"][0]["lockerAddr"] == ics.lockerWeights.address


    for locker in [ics.lockerSwap, ics.lockerWeights]:
        proposal_id = locker.proposalID()
        if proposal_id == 0:
            proposal = SwapProposal.at(ics.manager.trustedProposals(0))
        else:
            proposal = WeightProposal.at(ics.manager.trustedProposals(1))
        assert proposal.state() == consts.STATE_TO_NUM["Created"]

        # Out of my scope to test that the proposals were made correctly, only
        # need to test that they exist
        assert ics.manager.trustedProposals(proposal_id) != consts.ZERO_ADDRESS
        assert ics.manager.proposalsLength() == 2
        assert ics.locker_factory.proposalIDToLocker(proposal_id) == locker.address
        assert ics.locker_factory.lockerAddrToProposalID(locker.address) == proposal_id
        assert locker.lockerFactory() == ics.locker_factory.address
        assert locker.proposer() == a[2]
        startTime = ics.startTimeSwap if locker.proposalID() == 0 else ics.startTimeWeights
        assert locker.startTime() == startTime
        assert locker.RSR() == ics.rsr.address
        assert locker.lockLength() == consts.INITIAL_PROPOSAL_LOCK_TIME
        assert ics.rsr.balanceOf(locker.address) == consts.INITIAL_RSR_AMOUNT_TO_LOCK
        assert ics.rsr.balanceOf(ics.locker_factory.address) == 0
