from brownie import *
import pytest
import consts
from deploy_ics import deploy_ics


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# Initial contracts. It would be nice to not have to use `ics.` in all tests, but
# since pretty much all tests start from a state of all contracts being deployed
# it makes it cleaner to know for a fact that `ics` generates the same state every
# time, as opposed to using separate modules for each contract and using only
# 'some' of them in each test which 'should' have the same state as `ics`, which
# would give an opportunity for errors and therefore bugs in tests by starting
# with the wrong state by accident.
@pytest.fixture(scope="module")
def ics():
    yield deploy_ics()


# Creates a new locker with `lockAndProposeSwap` and adds it to `ics`
@pytest.fixture(scope="module")
def lockerSwap(ics):
    proposer = a[2]
    ics.rsr.approve(ics.locker_factory.address, consts.INITIAL_RSR_AMOUNT_TO_LOCK, {"from": proposer})
    amount_to_swap = 1e7
    ics.other_sc_a.approve(ics.manager.address, amount_to_swap, {"from": proposer})

    lockAndProposeSwapTx = ics.locker_factory.lockAndProposeSwap(
        [ics.usdc.address, ics.other_sc_a],
        [amount_to_swap, amount_to_swap],
        [False, True],
        {"from": proposer}
    )

    ics.startTimeSwap = lockAndProposeSwapTx.timestamp
    ics.lockerSwap = Locker.at(lockAndProposeSwapTx.return_value)

    return lockAndProposeSwapTx


# Creates a new locker with `lockAndProposeWeights` and adds it to `ics`
@pytest.fixture(scope="module")
def lockerWeights(ics):
    proposer = a[2]
    ics.rsr.approve(ics.locker_factory.address, consts.INITIAL_RSR_AMOUNT_TO_LOCK, {"from": proposer})

    # Since the basket weights are the same pre and post proposal, we can use this
    amounts = ics.manager.toIssue(ics.rsv.totalSupply())

    for i, sc in enumerate([ics.other_sc_a, ics.other_sc_b, ics.other_sc_c]):
        sc.approve(ics.manager.address, amounts[i], {"from": proposer})


    lockAndProposeWeightsTx = ics.locker_factory.lockAndProposeWeights(
        [ics.other_sc_a, ics.other_sc_b, ics.other_sc_c],
        consts.BASKET_WEIGHTS,
        {"from": proposer}
    )

    ics.startTimeWeights = lockAndProposeWeightsTx.timestamp
    ics.lockerWeights = Locker.at(lockAndProposeWeightsTx.return_value)

    return lockAndProposeWeightsTx


# Accepts the proposal created with `lockAndProposeSwap`
@pytest.fixture(scope="module")
def lockerSwapAccepted(ics, lockerSwap):
    ics.manager.acceptProposal(ics.lockerSwap.proposalID(), {'from': a.at(ics.manager.operator())})


# Accepts the proposal created with `lockAndProposeWeights`
@pytest.fixture(scope="module")
def lockerWeightsAccepted(ics, lockerWeights):
    ics.manager.acceptProposal(ics.lockerWeights.proposalID(), {'from': a.at(ics.manager.operator())})
