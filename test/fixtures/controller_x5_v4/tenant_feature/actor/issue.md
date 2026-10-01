# Feature result seen by the wrong tenant

A warm lookup returned another tenant's feature value. Backend routing,
cache identity and stale update handling are live explanations. A second
report says an update was not reflected in the next read. Inspect trace.json
and run probes that distinguish these causes before changing features.py.

Reads must use the requested tenant and feature. An update replaces only that
tenant's feature value. Preserve truthful source labels. Submit report.json
with observed probes, diagnosis, completion claim and next step. Leave the
adapter and public files unchanged.
