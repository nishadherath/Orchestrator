# Isolate report cache entries by tenant

Two tenants can request the same record number and receive different reports.
The current cache sometimes returns the first tenant's data to the second.
Include every contractually relevant input in the key while preserving valid
cache hits. Options are an unordered mapping of scalar values. Change only
`service/reports.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
