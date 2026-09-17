# Make the account migration resumable

The account store must add a required `email_domain` field to a populated
SQLite database. Deployments can stop after any committed backfill batch, and
the old writer continues inserting only `id` and `email` during the transition.
Preserve account IDs and data, make retries safe, keep the old writer working
before and after completion, and leave `email_domain` enforced as non-null.
Change only `store/migration.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
