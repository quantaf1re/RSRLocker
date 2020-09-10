from consts import *
from brownie import a, reverts, chain, Basket, SwapProposal, WeightProposal
from brownie.test import given, strategy


# Test that an accepted proposal can be executed any time after the 24h delay.
# +1 because of `>` rather than `>=` in `require(now > time, "wait to execute");'
@given(delay=strategy(
    "uint256",
    min_value=SECONDS_24H+1,
    max_value=SECONDS_1Y
))
def test_acceptProposal_executeProposal(a, ics, lockerSwapAccepted, lockerWeightsAccepted, delay):
    chain.sleep(delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        if locker.proposalID() == 0:
            proposal = SwapProposal.at(ics.manager.trustedProposals(0))
        else:
            proposal = WeightProposal.at(ics.manager.trustedProposals(1))
        assert proposal.state() == STATE_TO_NUM[ACCEPTED]
        original_basket = Basket.at(ics.manager.trustedBasket())

        ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})

        assert proposal.state() == STATE_TO_NUM[COMPLETED]
        assert original_basket.address != Basket.at(ics.manager.trustedBasket()).address


# `executeProposal` should fail if the 24h has not passed
@given(delay=strategy("uint256", max_value=SECONDS_24H))
def test_acceptProposal_executeProposal_revert(a, ics, lockerSwapAccepted, lockerWeightsAccepted, delay):
    # Because there's a difference between ics.lockerSwap.startTime() and this
    # test being called, that difference + SECONDS_24H can actually be more than
    # 24h and therefore cause this test to fail even though there's nothing
    # wrong with the contract. Therefore we need to set a max value on `delay`,
    # but because it depends on ics.lockerSwap.startTime(), it can't be called
    # in @given above. We'll use lockerSwap since it's always executed before
    # lockerWeights, but still retain @given's randomness
    last_time_to_fail = ics.startTimeSwap + SECONDS_24H
    max_delay = last_time_to_fail - chain.time()
    corrected_delay = min(delay, max_delay)
    chain.sleep(corrected_delay)

    for locker in [ics.lockerSwap, ics.lockerWeights]:
        with reverts("wait to execute"):
            ics.manager.executeProposal(locker.proposalID(), {'from': a.at(ics.manager.operator())})
