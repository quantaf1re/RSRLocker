import pytest
from deploy_ics import deploy_ics
from brownie import a, reverts, chain, Locker, SwapProposal, WeightProposal, BasicERC20, Basket
from consts import *

class _ICs():

    """
    This 'Initial Contracts' state machine class contains initialization and
    invariant methods that are shared across multiple stateful tests.
    """

    def __init__(cls, a):
        cls.a = a
        cls.ics = deploy_ics()


    # Atomically change balances
    def transfer_bals(self, bals, from_addr, to, amount):
        bals[str(from_addr)] -= amount
        if str(to) in bals:
            bals[str(to)] += amount
        else:
            bals[str(to)] = amount

    # Put info on the new locker in the local caches
    def register_created_locker(self, proposer, tx, is_swap):
        locker = Locker.at(tx.return_value)
        proposal_id = self.ics.locker_factory.lockerAddrToProposalID(locker.address)
        self.id_to_state[proposal_id] = CREATED
        self.id_to_start_time[proposal_id] = tx.timestamp
        self.id_to_locker[proposal_id] = locker
        self.id_to_proposal_is_swap[proposal_id] = is_swap
        if is_swap:
            self.id_to_proposal[proposal_id] = SwapProposal.at(self.ics.manager.trustedProposals(proposal_id))
        else:
            self.id_to_proposal[proposal_id] = WeightProposal.at(self.ics.manager.trustedProposals(proposal_id))
        self.transfer_bals(
            self.rsr_bals,
            proposer,
            tx.return_value,
            self.ics.locker_factory.RSRAmountToLock()
        )

    # Call lockAndProposeSwap and approve tokens that need to be approved for
    # execution to be successful only if:
    #  - the proposer has enough (accounting for any other proposals that have
    # been made but not executed, which eats more allowance)
    #  - the vault has enough tokens to execute the swap
    #  - the proposer has enough rsr to lock up
    def lock_and_propose_swap_single(self, token_out_vault, token_to_vault, amount_to_swap, proposer):
        enough_tokens_proposer = (token_to_vault.allowance(proposer, self.ics.manager.address) +
            amount_to_swap <= token_to_vault.balanceOf(proposer))
        # Check whether the vault has enough tokens to swap when executed
        enough_tokens_vault = (token_out_vault.balanceOf(self.ics.manager.trustedVault())
            >= amount_to_swap)
        enough_rsr = (self.ics.rsr.allowance(proposer, self.ics.manager.address) +
                self.ics.locker_factory.RSRAmountToLock() <=
                self.ics.rsr.balanceOf(proposer))

        def do_tx():
            self.ics.rsr.approve(
                self.ics.locker_factory.address,
                self.ics.locker_factory.RSRAmountToLock(),
                {"from": proposer}
            )
            # I'm treating other_sc_a as == to usdc, other_sc_b == tusd,
            # and other_sc_c == pax in terms of decimals to simplify things
            token_to_vault.increaseAllowance(
                self.ics.manager.address,
                amount_to_swap,
                {"from": proposer}
            )

            return self.ics.locker_factory.lockAndProposeSwap(
                [token_out_vault.address, token_to_vault.address],
                [amount_to_swap, amount_to_swap],
                [False, True],
                {"from": proposer}
            )

        # A quirk of the original Manager's behaviour is that proposals can be
        # proposed and accepted even if executing that proposal would revert
        # because the proposer doesn't have enough tokens or the vault doesn't
        # have enough tokens. Since that's not behaviour that was introduced
        # in this project, it's outside the scope of this to test it, and it's
        # simpler to ignore it by not allowing non-executable proposals to be
        # proposed.
        if enough_tokens_proposer and enough_tokens_vault and enough_rsr:
            tx = do_tx()
            self.register_created_locker(proposer, tx, True)

        elif not enough_rsr:
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
        enough_tokens = all(
            token.allowance(proposer, self.ics.manager.address) +
            amount <=
            token.balanceOf(proposer) for token, amount in zip(tokens, amounts))
        enough_rsr = (self.ics.rsr.allowance(proposer, self.ics.manager.address) +
            self.ics.locker_factory.RSRAmountToLock() <=
            self.ics.rsr.balanceOf(proposer))

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
            self.register_created_locker(proposer, tx, False)
        elif not enough_rsr:
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

            tx = self.ics.manager.acceptProposal(proposal_id, {"from": signer})
            self.id_to_state[proposal_id] = ACCEPTED
            self.id_to_accept_time[proposal_id] = tx.timestamp

        else:
            with reverts():
                self.ics.manager.acceptProposal(proposal_id, {"from": signer})

    # Call execute_proposal is:
    #  - the proposal exists
    #  - the proposal is accepted
    #  - the signer is the operator
    #  - 24h have passed from acceptance
    def execute_proposal(self, proposal_id, signer):
        if (proposal_id in self.id_to_state and
                self.has_tokens(proposal_id) and
                self.id_to_state[proposal_id] == ACCEPTED and
                signer == self.ics.manager.operator() and
                chain.time() - self.id_to_accept_time[proposal_id] > SECONDS_24H):

            self.ics.manager.executeProposal(proposal_id, {"from": signer})
            self.id_to_state[proposal_id] = COMPLETED

        else:
            with reverts():
                self.ics.manager.executeProposal(proposal_id, {"from": signer})

    # Checks whether the proposer and the current vault have enough tokens
    # for a given proposal to execute successfully
    def has_tokens(self, proposal_id):
        vault_addr = self.ics.manager.trustedVault()
        proposer = self.id_to_locker[proposal_id].proposer()
        proposal = self.id_to_proposal[proposal_id]

        if self.id_to_proposal_is_swap[proposal_id]:
            vault_has_enough = True
            proposer_has_enough = True
            # Since there's no way to get the length of an array outside the
            # contract, I'm relying on the fact that the length is always 2 here
            for i in range(2):
                token = BasicERC20.at(proposal.tokens(i))
                amount = proposal.amounts(i)
                if proposal.toVault(i) == True:
                    proposer_has_enough = (proposer_has_enough and
                        token.balanceOf(proposer) >= amount and
                        token.allowance(proposer, self.ics.manager) >= amount)
                else:
                    vault_has_enough = (vault_has_enough and
                        token.balanceOf(vault_addr) >= amount)

            return vault_has_enough and proposer_has_enough

        else:
            proposer_has_enough = True
            basket = Basket.at(proposal.trustedBasket())
            # Since the scope here is only to test new functionality, we can
            # just only test with the same weights but different tokens, so
            # amounts are the same
            amounts = self.ics.manager.toIssue(self.ics.rsv.totalSupply())
            tokens = basket.getTokens()
            for i in range(len(tokens)):
                token = BasicERC20.at(basket.tokens(i))
                proposer_has_enough = (proposer_has_enough and
                    token.balanceOf(proposer) > amounts[i])

            return proposer_has_enough



    # Call withdraw if:
    #  - proposal exists
    #  - 30d have passed
    def withdraw(self, proposal_id, signer):
        if (proposal_id in self.id_to_locker and
                chain.time() - self.id_to_start_time[proposal_id] >
                        self.ics.locker_factory.lockTime()):

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
