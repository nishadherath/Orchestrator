# Missing receipts after a queue reorder

The incident report blames queue reordering for receipts that no longer match
orders. The reproducible inputs include IDs issued by two clients, one with
uppercase prefixes and zero-padded numbers and the other with lowercase,
unpadded numbers. Accounts remain strict boundaries. Repair `reconcile.py`
to reconcile the documented aliases without joining distinct accounts or ID
prefixes. Preserve input order and return each order once. Keep the adapter
and public check unchanged. Submit `report.json` with a supported diagnosis,
causal probes, completion claim and safe next step.
