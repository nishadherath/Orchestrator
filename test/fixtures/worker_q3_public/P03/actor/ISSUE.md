# Inconsistent CLI typo diagnostics

A maintenance CLI now has enough subcommands and options that operators often
mistype one of them. A misspelled subcommand gives no useful hint, while a
misspelled option uses different wording and ordering. Improve the diagnostics
so a close name gets a concise suggestion, ambiguous names get a small sorted
set of suggestions, and unrelated names still fail without a misleading hint.
Keep normal command parsing and exit behaviour intact.

Run `python3 -B public_check.py` for the local smoke check. The permitted
source edits are `click/__init__.py`, `click/core.py`, `click/exceptions.py`
and `click/parser.py`. Do not edit the public check, issue, acceptance file,
other Click modules or licence. The evaluation includes option and command
variants beyond the smoke check.
