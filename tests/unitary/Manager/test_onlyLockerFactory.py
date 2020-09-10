import consts
from brownie import reverts
from brownie.test import given, strategy


# Tests that no functions related to creating or cancelling proposals can be
# called by accounts other than `lockerFactory`


def test_proposeSwap_revert(a, ics):
    for signer in a:
        with reverts("only locker factory"):
            ics.manager.proposeSwap(
                [ics.usdc.address, ics.other_sc_a],
                [1e23, 1e23],
                [False, True],
                signer,
                {"from": signer}
            )


def test_proposeWeights_revert(a, ics):
    for signer in a:
        with reverts("only locker factory"):
            ics.manager.proposeWeights(
                [ics.other_sc_a, ics.other_sc_b, ics.other_sc_c],
                consts.BASKET_WEIGHTS,
                signer,
                {"from": signer}
            )


def test_cancelProposal_revert(a, ics):
    for signer in a:
        with reverts("only locker factory"):
            ics.manager.cancelProposal(1, {"from": signer})
