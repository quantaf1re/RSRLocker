import pytest
from deploy_ics import deploy_ics
from brownie import a, reverts, chain, Locker
from consts import *

class _ICs():

    """
    This 'Initial Contracts' state machine class contains initialization and
    invariant methods that are shared across multiple stateful tests.
    """

    def __init__(cls, a):
        cls.a = a
        cls.ics = deploy_ics()


    def transfer_bals(self, bals, from_addr, to, amount):
        bals[str(from_addr)] -= amount
        if str(to) in bals:
            bals[str(to)] += amount
        else:
            bals[str(to)] = amount

    # Put info on the new locker in the local caches
    def register_created_locker(self, proposer, tx):
        locker = Locker.at(tx.return_value)
        proposal_id = self.ics.locker_factory.lockerAddrToProposalID(locker.address)
        self.id_to_state[proposal_id] = CREATED
        self.id_to_start_time[proposal_id] = tx.timestamp
        self.id_to_locker[proposal_id] = locker
        self.transfer_bals(self.rsr_bals, proposer, tx.return_value, self.ics.locker_factory.RSRAmountToLock())

    # Call lockAndProposeSwap and approve tokens that need to be approved for
    # execution to be successful only if:
    #  - the proposer has enough (accounting for any other proposals that have
    # been made but not executed, which eats more allowance)
    #  - the vault has enough tokens to execute the swap
    #  - the proposer has enough rsr to lock up
    def lock_and_propose_swap_single(self, token_out_vault, token_to_vault, amount_to_swap, proposer):
        enough_tokens_proposer = token_to_vault.allowance(proposer, self.ics.manager.address) + amount_to_swap <= token_to_vault.balanceOf(proposer)
        # Check whether the vault has enough tokens to swap when executed
        enough_tokens_vault = token_out_vault.balanceOf(self.ics.manager.trustedVault())
        enough_rsr = (self.ics.rsr.allowance(proposer, self.ics.manager.address) +
                self.ics.locker_factory.RSRAmountToLock() <=
                self.ics.rsr.balanceOf(proposer))

        def do_tx():
            self.ics.rsr.approve(self.ics.locker_factory.address, self.ics.locker_factory.RSRAmountToLock(), {"from": proposer})
            # I'm treating other_sc_a as == to usdc, other_sc_b == tusd,
            # and other_sc_c == pax in terms of decimals to simplify things
            token_to_vault.increaseAllowance(self.ics.manager.address, amount_to_swap, {"from": proposer})

            return self.ics.locker_factory.lockAndProposeSwap(
                [token_to_vault.address, token_out_vault.address],
                [amount_to_swap, amount_to_swap],
                [False, True],
                {"from": proposer}
            )

        if enough_tokens_proposer and enough_tokens_vault and enough_rsr:
            tx = do_tx()
            self.register_created_locker(proposer, tx)
        else:
            with reverts():
                do_tx()

    # Call lockAndProposeWeights and approve tokens that need to be approved for
    # execution to be successful only if:
    #  - the proposer has enough (accounting for any other proposals that have
    # been made but not executed, which eats more allowance)
    #  - the proposer has enough rsr to lock up
    def lock_and_propose_weights(self, tokens, proposer):
        # Since the basket weights are the same pre and post proposal, we can use this
        amounts = self.ics.manager.toIssue(self.ics.rsv.totalSupply())
        enough_tokens = all(token.allowance(proposer, self.ics.manager.address) + amount <= token.balanceOf(proposer) for token, amount in zip(tokens, amounts))
        enough_rsr = self.ics.rsr.allowance(proposer, self.ics.manager.address) + self.ics.locker_factory.RSRAmountToLock() <= self.ics.rsr.balanceOf(proposer)

        def do_tx():
            self.ics.rsr.approve(
                self.ics.locker_factory.address,
                self.ics.locker_factory.RSRAmountToLock(),
                {"from": proposer}
            )

            for i, sc in enumerate([self.ics.other_sc_a, self.ics.other_sc_b, self.ics.other_sc_c]):
                sc.increaseAllowance(self.ics.manager.address, amounts[i], {"from": proposer})

            return self.ics.locker_factory.lockAndProposeWeights(
                tokens,
                BASKET_WEIGHTS,
                {"from": proposer}
            )

        if enough_tokens and enough_rsr:
            tx = do_tx()
            self.register_created_locker(proposer, tx)
        else:
            with reverts():
                do_tx()

    # Call cancelAndUnlock if:
    #  - the proposal exists
    #  - the proposal hasn't been completed already
    #  - the signer is one of [owner, operator, proposer]
    def cancel_proposal(self, proposal_id, signer):
        # Annoyingly, can't do `locker = self.id_to_locker[proposal_id]`
        # before checking if it exists
        # These are just getting too long...
        if (proposal_id in self.id_to_state and
                self.id_to_state[proposal_id] != COMPLETED and
                signer in [
                    self.ics.manager.owner(),
                    self.ics.manager.operator(),
                    self.id_to_locker[proposal_id].proposer()
                ]):

            locker = self.id_to_locker[proposal_id]
            self.id_to_state[proposal_id] = CANCELLED

            bal = self.ics.rsr.balanceOf(locker.address)
            if bal != 0:
                self.transfer_bals(self.rsr_bals, locker.address, locker.proposer(), bal)

            self.ics.locker_factory.cancelAndUnlock(proposal_id, {"from": signer})

        else:
            # We can call this with reverts here because it'll revert
            # even if the proposal doesn't exist since the contract we're
            # actually calling (locker_factory) does indeed already exist
            with reverts():
                self.ics.locker_factory.cancelAndUnlock(proposal_id, {"from": signer})

    # Call acceptProposal if:
    #  - the proposal exists
    #  - the proposal has only been created
    #  - the signer is the operator
    def accept_proposal(self, proposal_id, signer):
        if (proposal_id in self.id_to_state and
                self.id_to_state[proposal_id] == CREATED and
                signer == self.ics.manager.operator()):

            self.ics.manager.acceptProposal(proposal_id, {"from": signer})
            self.id_to_state[proposal_id] = ACCEPTED

        else:
            with reverts():
                self.ics.manager.acceptProposal(proposal_id, {"from": signer})

    def execute_proposal(self, proposal_id, signer):
        if (proposal_id in self.id_to_state and
                self.id_to_state[proposal_id] == ACCEPTED and
                signer == self.ics.manager.operator() and
                chain.time() - self.id_to_locker[proposal_id].startTime() > SECONDS_24H):

            self.ics.manager.executeProposal(proposal_id, {"from": signer})
            self.id_to_state[proposal_id] = COMPLETED

        else:
            with reverts():
                self.ics.manager.executeProposal(proposal_id, {"from": signer})

    def withdraw(self, proposal_id, signer):
        if proposal_id in self.id_to_locker and chain.time() - self.id_to_locker[proposal_id].startTime() > self.ics.locker_factory.lockTime():
            locker = self.id_to_locker[proposal_id]
            bal = self.ics.rsr.balanceOf(locker.address)
            if bal != 0:
                self.transfer_bals(self.rsr_bals, locker.address, locker.proposer(), bal)
            locker.withdraw({"from": signer})

        else:
            # We can't test if anything reverts in this case beause if the
            # locker doesn't exist then `Locker.at()' won't work with `reverts()`

            # with reverts("too early or wrong signer"):
            #     locker.withdraw({"from": signer})
            pass

    def fast_forward(self, amount):
        chain.sleep(amount)


@pytest.fixture
def ICs():
    yield _ICs















































#
