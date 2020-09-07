# RSRLocker

Because some contracts from RSR and RSV-V2 have the same name, it caused a namespace conflict with brownie. I would've liked to have made a single zeppelin/library that both rsr and rsv-v2 use, but because some of them have different code, I couldn't be sure that it wouldn't break anything or cause things to behave unexpectedly, and I would therefore have to test all the old code, which is outside of the scope of this project. Where the namespaces conflicted, I changed the `pragma 0.5.7` (rsv-v2) versions to be `___V2`. It's kind of a hacky way of doing it, but there wasn't really a choice without testing everything.