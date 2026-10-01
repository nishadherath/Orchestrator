# Preserve backslash round-trips and parser boundaries

`dotenv.set_key` must preserve values with consecutive backslashes when the
file is read back through `dotenv_values`. A quoted value ending in an escaped
backslash must terminate at its own quote so the next binding remains separate.
Preserve ordinary single-backslash values, plain values and existing quote
behaviour. The repair may change only `src/dotenv/main.py` and
`src/dotenv/parser.py`.

Run `python3 -B public_check.py`. It is a basic public smoke test; include
your own checks for the stated backslash and parser-boundary requirements.
Do not change this issue, the check, acceptance metadata or licence.
