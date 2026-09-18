# Complete the parsed-order result migration

The order package is replacing its anonymous `(order, warnings)` tuple with an
immutable `ParseResult` object exposing named `order` and `warnings` fields.
Complete the migration across the parser, storage adapter, CLI, batch consumer
and package exports. `ParseResult` must not be a tuple, and every packaging
entry point must use the new contract. Change only the files listed in the
fixture catalogue.

Run `python -m unittest discover -s public_checks -v` from the repository root.
