from brownie import a, reverts, chain, SwapProposal, WeightProposal
from brownie.test import strategy
from consts import *


# Change settings as desired
# default = {"stateful_step_count": 10, "max_examples": 50}
settings = {"stateful_step_count": 50, "max_examples": 50}


# Note: rarely this test fails because of a timeout error which is a bug in
# brownie.
def test_stateful_all_proposals(ICs, state_machine, Locker, a):

    """
    Stateful test that verifies proposals can overlap arbitrarily.
    """

    class StateMachine(ICs):

        st_addr = strategy("address")
        # 1.5 x the starting amount of each 18 decimal coin (tusd, pax)
        # collateralising rsv such that sometimes it'll be too much
        st_uint = strategy("uint", max_value=10**20)
        st_uint_usdc = strategy("uint", max_value=10**8)
        # Since there's only 4 possible proposals
        st_proposal_id = strategy("uint256", max_value=3)

        def setup(self):
            # Gonna have to use `str()` on keys otherwise we get
            # `TypeError: unhashable type: 'EthAddress'` when inputing contracts
            # and `No account exists for ___` when using contracts as accounts
            self.rsr_bals = {str(ac): 10**47 for ac in self.a}
            self.id_to_state = {}
            self.id_to_locker = {}
            self.id_to_start_time = {}
            self.id_to_accept_time = {}


        # ---------------------- Rules ----------------------

        # proposeSwap

        def rule_lock_and_propose_swap_single_0(self, st_uint_usdc, st_addr):
            self.lock_and_propose_swap_single(
                self.ics.usdc, self.ics.other_sc_a, st_uint_usdc, st_addr)

        def rule_lock_and_propose_swap_single_1(self, st_uint, st_addr):
            self.lock_and_propose_swap_single(
                self.ics.tusd, self.ics.other_sc_b, st_uint, st_addr)

        # proposeWeights

        def rule_lock_and_propose_weights_0(self, st_addr):
            self.lock_and_propose_weights(
                [self.ics.other_sc_a, self.ics.other_sc_b, self.ics.other_sc_c], st_addr)

        def rule_lock_and_propose_weights_1(self, st_addr):
            self.lock_and_propose_weights(
                [self.ics.usdc, self.ics.other_sc_b, self.ics.other_sc_c], st_addr)

        # cancelProposal

        def rule_cancel_proposal_0(self, st_proposal_id, st_addr):
            self.cancel_proposal(st_proposal_id, st_addr)

        def rule_cancel_proposal_1(self, st_proposal_id, st_addr):
            self.cancel_proposal(st_proposal_id, st_addr)

        def rule_cancel_proposal_2(self, st_proposal_id, st_addr):
            self.cancel_proposal(st_proposal_id, st_addr)

        # acceptProposal

        def rule_accept_proposal_0(self, st_proposal_id, st_addr):
            self.accept_proposal(st_proposal_id, st_addr)

        def rule_accept_proposal_1(self, st_proposal_id, st_addr):
            self.accept_proposal(st_proposal_id, st_addr)

        def rule_accept_proposal_2(self, st_proposal_id, st_addr):
            self.accept_proposal(st_proposal_id, st_addr)

        # executeProposal

        def rule_execute_proposal_0(self, st_proposal_id, st_addr):
            self.execute_proposal(st_proposal_id, st_addr)

        def rule_execute_proposal_1(self, st_proposal_id, st_addr):
            self.execute_proposal(st_proposal_id, st_addr)

        def rule_execute_proposal_2(self, st_proposal_id, st_addr):
            self.execute_proposal(st_proposal_id, st_addr)

        # withdraw

        def rule_withdraw_0(self, st_proposal_id, st_addr):
            self.withdraw(st_proposal_id, st_addr)

        def rule_withdraw_1(self, st_proposal_id, st_addr):
            self.withdraw(st_proposal_id, st_addr)

        def rule_withdraw_2(self, st_proposal_id, st_addr):
            self.withdraw(st_proposal_id, st_addr)

        # fast forward 30d

        def rule_fast_forward_30d_0(self):
            self.fast_forward(INITIAL_PROPOSAL_LOCK_TIME+1)

        def rule_fast_forward_30d_1(self):
            self.fast_forward(INITIAL_PROPOSAL_LOCK_TIME+1)

        def rule_fast_forward_30d_2(self):
            self.fast_forward(INITIAL_PROPOSAL_LOCK_TIME+1)

        # fast forward 24h

        def rule_fast_forward_24h_0(self):
            self.fast_forward(SECONDS_24H+1)

        def rule_fast_forward_24h_1(self):
            self.fast_forward(SECONDS_24H+1)

        def rule_fast_forward_24h_2(self):
            self.fast_forward(SECONDS_24H+1)


        # ---------------------- Invariants ----------------------

        # I'm assuming that `proposeSwap` and `proposeWeights` work fine as
        # it's outside the scope of this, therefore don't need to track
        # non-rsr balances

        def invariant_num_proposals(self):
            assert len(self.id_to_state) == self.ics.manager.proposalsLength()
            assert len(self.id_to_state) == len(self.id_to_start_time)
            assert len(self.id_to_state) == len(self.id_to_locker)

        def invariant_rsr_bals(self):
            for addr, bal in self.rsr_bals.items():
                assert self.ics.rsr.balanceOf(addr) == bal

        def invariant_states(self):
            for proposal_id, state in self.id_to_state.items():
                # This will instantiate some `WeightProposal`s as `SwapProposal`s
                # but since we're only testing `state`, which is common to both
                # by definition, it's fine
                proposal = SwapProposal.at(self.ics.manager.trustedProposals(proposal_id))
                assert proposal.state() == STATE_TO_NUM[state]


    state_machine(StateMachine, a, settings=settings)
