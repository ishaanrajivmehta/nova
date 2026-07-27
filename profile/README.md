# profile/ — your private vault

Empty by default. `/nova:setup-cvprofile` populates it.

Everything here is yours: real employment history, contact details, application record. It never leaves
your machine, and the repo's `.gitignore` refuses to track anything in this folder except this file.

Point `craft` at a profile in any of three ways (checked in order):

1. `--profile /path/to/profile`
2. this folder
3. `$NOVA_PROFILE`

With a profile, crafting uses your real shapeable angles, project pool and stretch history. Without one,
the vault is reconstructed from whatever CV you supply — workable, but thinner.
