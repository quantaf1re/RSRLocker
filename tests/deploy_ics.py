from brownie import *
from consts import *


class Context:
    pass


# Initial contracts. It would be nice to not have to use `ics.` in all tests, but
# since pretty much all tests start from a state of all contracts being deployed
# it makes it cleaner to know for a fact that `ics` generates the same state every
# time, as opposed to using separate modules for each contract and using only
# 'some' of them in each test which 'should' have the same state as `ics`, which
# would give an opportunity for errors and therefore bugs in tests by starting
# with the wrong state by accident.
def deploy_ics():
    owner = a[0]
    daily = a[1]
    temp = a[2]

    owner_signer = {"from": owner}
    daily_signer = {"from": daily}
    temp_signer = {"from": temp}

    # -----Contracts pre-upgrade-----

    # Make USDC, TUSD, and PAX exist
    usdc = BasicERC20.deploy(owner_signer)
    tusd = BasicERC20.deploy(owner_signer)
    pax = BasicERC20.deploy(owner_signer)

    # Now begin our contracts
    vault = Vault.deploy(owner_signer)
    rsv = PreviousReserve.deploy(owner_signer)

    # It would be nice to use `ReserveRightsToken` directly, but it requires
    # `previousContract` which would have to be an `BasicERC20` anyway. They
    # should both act exactly the same as ERC20s where founders' addresses aren't
    # concerned.
    rsr = BasicERC20.deploy(owner_signer)
    locker_factory = LockerFactory.deploy(
        rsr.address,
        INITIAL_PROPOSAL_LOCK_TIME,
        INITIAL_RSR_AMOUNT_TO_LOCK,
        owner_signer
    )

    proposal_factory = ProposalFactory.deploy(owner_signer)
    basket = Basket.deploy(
        ZERO_ADDRESS,
        [usdc.address, tusd.address, pax.address],
        BASKET_WEIGHTS,
        owner_signer,
    )
    manager = Manager.deploy(
        vault.address,
        rsv.address,
        proposal_factory.address,
        basket.address,
        daily.address,
        0,
        locker_factory,
        owner_signer,
    )
    locker_factory.setManager(manager.address, owner_signer)

    vault.changeManager(manager.address, owner_signer)
    rsv.changeMinter(manager.address, owner_signer)
    rsv.changePauser(daily.address, owner_signer)
    rsv.changeFeeRecipient(daily.address, owner_signer)
    rsv.unpause(daily_signer)
    manager.setEmergency(False, daily_signer)

    usdc.approve(manager.address, 100000200, owner_signer)  # $100.0002 fC
    tusd.approve(
        manager.address, 99999900000000000000, owner_signer
    )  # $99.9999 TUSD
    pax.approve(
        manager.address, 99999900000000000000, owner_signer
    )  # $99.9999 PAX

    manager.issue(3e20, owner_signer)  # $300 RSV
    assert rsv.totalSupply() == 3e20


    # -----V2 upgrade 1st half-----

    # Deploy New RSV
    rsv_2 = Reserve.deploy(temp_signer)
    rsv_2.nominateNewOwner(owner.address, temp_signer)

    # Create the new manager and update others to point to it
    manager_2 = Manager.deploy(
        vault.address,
        rsv_2.address,
        proposal_factory.address,
        basket.address,
        daily.address,
        0,
        locker_factory,
        temp_signer,
    )
    manager_2.nominateNewOwner(owner.address, temp_signer)
    locker_factory.setManager(manager_2.address, owner_signer)

    # Deploy relayer
    relayer = Relayer.deploy(rsv_2.address, temp_signer)
    relayer.nominateNewOwner(owner.address, temp_signer)

    # Set the new RSV to point to all the right things
    rsv_2.changeRelayer(relayer.address, temp_signer)
    rsv_2.changeMinter(manager_2.address, temp_signer)
    rsv_2.changePauser(daily.address, temp_signer)
    rsv_2.changeFeeRecipient(daily.address, temp_signer)


    # -----V2 upgrade 2nd half-----

    # Pause the old manager
    manager.setEmergency(True, daily_signer)

    # Transfer all owners to the permanent owner key
    rsv_2.acceptOwnership(owner_signer)
    relayer.acceptOwnership(owner_signer)
    manager_2.acceptOwnership(owner_signer)

    # Set the vault to point to the new manager
    vault.changeManager(manager_2.address, owner_signer)

    # Finalize the fork
    rsv.nominateNewOwner(rsv_2.address, owner_signer)
    rsv_2.acceptUpgrade(rsv.address, owner_signer)

    # Unpause the new manager
    manager_2.setEmergency(False, daily_signer)


    # -----Final confirmations, might aswell-----
    # Check redemptions
    assert rsv_2.totalSupply() == 3e20
    rsv_2.approve(manager_2.address, 2e20, owner_signer)
    manager_2.redeem(2e20, owner_signer)
    assert rsv_2.totalSupply() == 1e20
    print("successfully redeemed!")

    # Check issuance

    # usdc.approve(manager_2.address, 100000200, owner_signer)  # $100.0002 USDC
    # tusd.approve(
    #     manager_2.address, 99999900000000000000, owner_signer
    # )  # $99.9999 TUSD
    # pax.approve(
    #     manager_2.address, 99999900000000000000, owner_signer
    # )  # $99.9999 PAX
    # manager_2.issue(3e20, owner_signer)
    # assert rsv_2.totalSupply() == 4e20

    rsv_amount_to_create = 1e20
    collat_amounts = manager_2.toIssue(rsv_amount_to_create)
    for i, token in enumerate([usdc, tusd, pax]):
        token.approve(manager_2.address, collat_amounts[i], owner_signer)
    manager_2.issue(rsv_amount_to_create, owner_signer)
    print("and issued!")

    # -----Copied from the rsv-v2 upgrade, might aswell use it-----

    # Make sure the old stuff is turned off
    assert rsv.paused()
    assert manager.emergency()

    # Make sure the vault points to the new manager
    assert vault.manager() == manager_2.address

    # Check the entire new Manager state
    assert manager_2.operator() == daily.address
    assert manager_2.trustedBasket() == basket.address
    assert manager_2.trustedVault() == vault.address
    assert manager_2.trustedRSV() == rsv_2.address
    assert manager_2.trustedProposalFactory() == proposal_factory.address
    assert manager_2.proposalsLength() == 0
    assert not manager_2.issuancePaused()
    assert not manager_2.emergency()
    assert manager_2.seigniorage() == 0

    # Check the entire new RSV state
    assert rsv_2.getEternalStorageAddress() == rsv.getEternalStorageAddress()
    assert rsv_2.trustedTxFee() == ZERO_ADDRESS
    assert rsv_2.trustedRelayer() == relayer.address
    assert rsv_2.maxSupply() == rsv.maxSupply()
    assert not rsv_2.paused()
    assert rsv_2.minter() == manager_2.address
    assert rsv_2.pauser() == daily.address
    assert rsv_2.feeRecipient() == daily.address

    # Make sure the bridge is burnt behind us
    assert rsv.minter() == ZERO_ADDRESS
    assert rsv.pauser() == ZERO_ADDRESS
    assert rsv.owner() == ZERO_ADDRESS
    assert rsv.paused()


    # -----Additions for RSR locking-----

    # So these coins can be swapped out and used for stateful testing
    other_stablecoins = []
    for i in range(3):
        sc = BasicERC20.deploy(owner_signer)
        other_stablecoins.append(sc)


    # So everyone can create proposals
    tokens = [rsr] + other_stablecoins + [usdc, tusd, pax]
    for token in tokens:
        for j in range(1, 10):
            token.transfer(a[j], 1e47, owner_signer)


    ctx = Context()
    ctx.usdc = usdc
    ctx.tusd = tusd
    ctx.pax = pax
    ctx.rsr = rsr
    ctx.other_sc_a = other_stablecoins[0]
    ctx.other_sc_b = other_stablecoins[1]
    ctx.other_sc_c = other_stablecoins[2]
    ctx.basket = basket
    ctx.vault = vault
    ctx.rsv = rsv_2
    ctx.relayer = relayer
    ctx.proposal_factory = proposal_factory
    ctx.locker_factory = locker_factory
    ctx.manager = manager_2

    return ctx
