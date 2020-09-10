# RSRLocker

The `master` branch doesn't contain any of my changes - only the original `rsr` and `rsv-v2` repos put into the same repo. This was done so that changes I made are easier to see in the PR from `addLocker` to `master`.

I also added `oldProjectIncentiveProposalsProof.pdf` to this repo incase you're interested, which is the proof of why the previous project proposal of incentivising RSV transactions with a set amount of RSR per unit time in a zero sum game is exploitable and won't work. Spoiler: tractor go brrr 🤠

## Design choices
I chose to route all the new logic through `LockerFactory`, which manifested in adding a new modifier `onlyLockerFactory` to `proposeSwap`, `proposeWeights`, and `cancelProposal` in `Manager`, which forces those functions to only be able to be called by `lockAndProposeSwap`, `lockAndProposeWeights`, and `cancelAndUnlock` respectively. This was partly because the changes to `Manager` were to be as minimal as possible, but mainly because it forces the creation and cancellation of proposals to be atomic and guarantees that `LockerFactory` always knows about proposal changes that are relevant to RSR being locked up, which reduces the complexity and attack surface, therefore making the system more secure. No checks on any RSR balances are needed in `Manager` because it is guaranteed that RSR has been locked up by `LockerFactory` in a new `Locker`. Cancellation can happen even if a proposer has already withdrawn their RSR (after the 30d).

A factory was chosen for creating new lockers because it conceptually and concretely separates the RSR locked up between different proposals, which allows the system to be more modular and secure since some bug that allows a user to withdraw tokens in one locker can only affect one locker, ensuring they cannot withdraw more than they deposited and cannot affect other propsers' deposits.

The logic flow is designed in such a way that functions can be executed in arbitrary orders (verified by the `test_all_proposals` stateful test) while still retaining the properties:
 - RSR is locked up at the time of proposal creation
 - RSR can be withdrawn after 30 days
 - cancellation can happen at any time (unless the proposal is already completed), even if funds have already been withdrawn (after 30 days)
 - cancellation refunds the proposer if the proposer hasn't already withdrawn the locked RSR
 - proposals can only be executed 24h after acceptance


## Zeppelin & file structure
Because some contracts from RSR and RSV-V2 have the same name, it caused a namespace conflict with brownie. I would've liked to have made a single zeppelin/library that both rsr and rsv-v2 use, but because some of them have different code, I couldn't be sure that it wouldn't break anything or cause things to behave unexpectedly, and I would therefore have to test all the old code, which is outside of the scope of this project. Where the namespaces conflicted, I changed the `pragma 0.5.7` (rsv-v2) versions to be `___V2`. It's kind of a hacky way of doing it, but there wasn't really a choice without retesting everything.


## Tools used to test

### Brownie testing:
 - unit tests
 - integration tests
 - stateful test

All tests pass (it takes roughly 15m for stateful and 10m for non-stateful)

### MythX:
No issues found other than mentioning that the solidity version used (`0.5.7`) is outdated and that time used in the contracts, such as `now`, can be manipulated to a certain extent by malicious miners. Since the system is already fine with using time to measure 24h, it's fine for me to use it to measure 30d.
Generated report is in `toolReports`.

### Slither
The only issues found other than the ones found with MythX were:
 - complaints about naming `not in mixedCase`, which is just aesthetic and I copied the style already used throughout `rsv-v2`
 - `owner() should be declared external` in `rsv-v2/ownership/OwnableV2.sol`, but that's outside of the scope of this project

### Manticore
I haven't gone into too much detail with Manticore, but from some initial tests, the only warning is about the use of time (`now` etc) in the contracts, same as the above tools.
