adding `hardstops` like (, [, { to not expand if these are infront of a chip and stop chunking from looking past them
this could avoid false positives when expanding code and math though at this phase it is unclear how common of an occurrence that will be
especially if _ is set to be ignore by chunking already

some sort of auto generation for the config.py or the example config so there is only one source of truth.
Codegen would be nice because it may allow the possiblity to detect non-existing options set in a config, and suggest the closes one.

