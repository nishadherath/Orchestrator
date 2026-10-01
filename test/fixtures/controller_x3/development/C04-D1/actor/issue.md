# Feature cache returns another tenant's value

The service stores a feature value after a tenant-specific lookup. The cache
then answers later lookups without a database call. A support trace shows a
tenant receiving another tenant's feature value after a warm-up request.
Repair `cache.py` so cache identity includes the tenant and feature, updates
replace the tenant's earlier value, and unrelated features remain separate.
Keep the adapter and public check unchanged. Submit `report.json` with a
supported diagnosis, causal probes, completion claim and safe next step.
