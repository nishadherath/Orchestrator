# Online profile migration read regression

An online migration is moving numeric profile values from `legacy` to
`current`. Old rows remain in service during backfill. A recent read-path
change returns missing values for those rows; the migration must not overwrite
a newer `current` value. Repair `migration.py` for reads and backfill while
preserving record order and zero as a legitimate value. Keep the adapter and
public check unchanged. Submit `report.json` with a completion claim,
diagnosis, causal observations and safe rollout step.
