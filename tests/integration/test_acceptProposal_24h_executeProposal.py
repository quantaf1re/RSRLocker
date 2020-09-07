import consts
from brownie import a, reverts, chain, Basket, SwapProposal, WeightProposal
from brownie.test import given, strategy


# Test that an accepted proposal can be executed any time after the 24h delay.
# +1 because of `>` rather than `>=` in `require(now > time, "wait to execute");'
@given(delay=strategy(
    "uint256",
    min_value=consts.SECONDS_24H+1,
    max_value=consts.SECONDS_1Y
))
def test_acceptProposal_executeProposal(a, ics, lockerSwapAccepted, lockerWeightsAccepted, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        if locker.proposalID() == 0:
            proposal = SwapProposal.at(ics.manager.trustedProposals(0))
        else:
            proposal = WeightProposal.at(ics.manager.trustedProposals(1))
        assert proposal.state() == consts.STATE_TO_NUM["Accepted"]
        originalBasket = Basket.at(ics.manager.trustedBasket())

        ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})

        assert proposal.state() == consts.STATE_TO_NUM["Completed"]
        assert originalBasket.address != Basket.at(ics.manager.trustedBasket()).address


# `executeProposal` should fail if the 24h has not passed
@given(delay=strategy("uint256", max_value=consts.SECONDS_24H))
def test_acceptProposal_executeProposal_revert(a, ics, lockerSwapAccepted, lockerWeightsAccepted, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        with reverts("wait to execute"):
            ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})
