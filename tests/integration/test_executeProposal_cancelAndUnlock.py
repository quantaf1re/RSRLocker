import consts
from brownie import a, reverts, chain, Basket, SwapProposal, WeightProposal
from brownie.test import given, strategy


# Test that a proposal that's already been executed can't be cancelled
# +1 because of `>` rather than `>=` in `require(now > time, "wait to execute");'
@given(delay=strategy(
    "uint256",
    min_value=consts.SECONDS_24H+1,
    max_value=consts.SECONDS_1Y
))
def test_executeProposal_cancelAndUnlock_revert(a, ics, lockerSwapAccepted, lockerWeightsAccepted, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        if locker.proposalID() == 0:
            proposal = SwapProposal.at(ics.manager.trustedProposals(0))
        else:
            proposal = WeightProposal.at(ics.manager.trustedProposals(1))
        assert proposal.state() == consts.STATE_TO_NUM["Accepted"]
        original_basket = Basket.at(ics.manager.trustedBasket())

        ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})
        assert proposal.state() == consts.STATE_TO_NUM["Completed"]

        with reverts():
            ics.locker_factory.cancelAndUnlock(locker.proposalID(), {'from': a.at(locker.proposer())})

        assert original_basket.address != Basket.at(ics.manager.trustedBasket()).address
        assert proposal.state() == consts.STATE_TO_NUM["Completed"]
