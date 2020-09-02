import pytest
import consts


@pytest.fixture(scope="module")
# Initial contracts
def ics(accounts, BasicERC20, Basket, Vault, Reserve, Relayer, ProposalFactory, LockerFactory, Manager):
    basket_weights = [333334e18, 333333e30, 333333e30]
    min_owner_wei = 300000000000000000  # 0.3 ETH
    min_daily_wei = 30000000000000000  # 0.03 ETH

    owner = accounts[0]
    daily = accounts[1]
    owner_signer = {"from": owner}
    daily_signer = {"from": daily}

    usdc = BasicERC20.deploy(owner_signer)
    tusd = BasicERC20.deploy(owner_signer)
    pax = BasicERC20.deploy(owner_signer)
    rsr = BasicERC20.deploy(owner_signer)
    basket = Basket.deploy(
        consts.ZERO_ADDRESS,
        [usdc.address, tusd.address, pax.address],
        basket_weights,
        owner_signer,
    )
    vault = Vault.deploy(owner_signer)
    rsv = Reserve.deploy(owner_signer)
    relayer = Relayer.deploy(rsv.address, owner_signer)
    rsv.changeRelayer(relayer.address)

    # TODO: make this work by resolving namespace conflict over `balance`
    # eternal_storage = ReserveEternalStorage.at(rsv.getEternalStorageAddress())
    # eternal_storage.acceptOwnership(owner_signer)

    proposal_factory = ProposalFactory.deploy(owner_signer)

    locker_factory = LockerFactory.deploy(rsr.address, consts.INITIAL_PROPOSAL_LOCK_TIME, consts.INITIAL_RSR_AMOUNT_TO_LOCK, owner_signer)

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
    print('|||||||||||||||||||||||||||||||||||||||||| manager')
    print(manager.address)

    locker_factory.setManager(manager, owner_signer)
    vault.changeManager(manager.address, owner_signer)
    rsv.changeMinter(manager.address, owner_signer)
    rsv.changePauser(daily.address, owner_signer)
    rsv.changeFeeRecipient(daily.address, owner_signer)
    rsv.unpause(daily_signer)
    manager.setEmergency(False, daily_signer)

    # Simple attribute dictionary
    class AttrDict(dict):
        def __init__(self, *args, **kwargs):
            super(AttrDict, self).__init__(*args, **kwargs)
            self.__dict__ = self

    # return usdc, tusd, pax, rsr, basket, vault, rsv, relayer, rsv, proposal_factory, locker_factory, manager

    # We either have 1 module like this or a separate module for each contract.
    # While this way is not ideal, I thought it was cleaner to have all the deployment
    # logic in a single place rather than split up over many modules. It also
    # allowed `owner` & `owner_signer` to be used without having to redefine it
    # in every single module, as would be needed with a separate module per contract
    return AttrDict({
        'usdc': usdc,
        'tusd': tusd,
        'pax': pax,
        'rsr': rsr,
        'basket': basket,
        'vault': vault,
        'rsv': rsv,
        'relayer': relayer,
        'rsv': rsv,
        'proposal_factory': proposal_factory,
        'locker_factory': locker_factory,
        'manager': manager
    })


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass
