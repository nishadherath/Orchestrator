# Make interrupted imports resumable

The importer persists its progress, but an interruption can cause an item to be
lost. Make each committed item and its checkpoint durable as one state change.
Rerunning after interruption must produce every item once, preserve unknown
state metadata, and remain safe after completion. Change only `importer/state.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
