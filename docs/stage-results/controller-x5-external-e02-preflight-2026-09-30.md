# X5 external E02: Alembic batch CHECK preflight

Date: 2026-09-30 Australia/Sydney. Status: **symptom reproduced, rejected for
paid X5 screening**. No worker or Controller provider call occurred. The
machine record is `test/results/2026-09-30-controller-x5-external-e02-preflight.json`.

The original [Alembic issue #1768](https://github.com/sqlalchemy/alembic/issues/1768)
reports duplicate Boolean CHECK constraints after a SQLite batch migration.
It names Alembic 1.17.2, SQLAlchemy 2.0.45 and Python 3.13.9. The public
issue body supplies a migration fragment but not a complete executable
database setup. The small [local reproduction](../../test/fixtures/controller_x5_external/development/E02/repro/repro.py)
uses the reported versions and the essential batch add of a named Boolean
column. It omits unrelated user, organisation and role columns and the old
status-column removal. This is an adaptation, not an exact replay of the
issue's schema. Dependencies were installed only in isolated host temp
locations. WSL used pinned Linux wheels unpacked into `/tmp` because its
Python has no `pip` or `ensurepip` module.

| Check | Windows Python 3.12.14 | WSL worker Python 3.14.7 |
| --- | --- | --- |
| Direct table creation, same named Boolean column | One CHECK | One CHECK |
| Before batch add | Zero CHECKs | Zero CHECKs |
| After batch add | Two identical `is_active` CHECKs | Two identical `is_active` CHECKs |
| Direct SQL insert of `is_active=2` | Rejected by SQLite CHECK | Rejected by SQLite CHECK |

The reproduced symptom is narrower than the issue's printed SQL. In the
report, the duplicated constraints have raw and convention-applied names;
in this adaptation, both have the raw `is_active` name. The execution did not
show a data-integrity bypass. The duplication could create future migration
or naming trouble, but that impact is an inference from the schema, not an
observed failure in this case. Related upstream reports now describe other
batch CHECK problems, including [naming drift](https://github.com/sqlalchemy/alembic/issues/1844)
and [silent omission of unnamed constraints](https://github.com/sqlalchemy/alembic/issues/1846).
Selecting one of those later discoveries as a protected failure after seeing
them would bias the case design.

E02 therefore fails the predeclared X5 requirement for a consequential,
independently qualified public residual-risk trigger. No repair, protected
oracle, wrong-repair control, matched root or sample plan was frozen. Do not
dispatch a paid producer or S/A continuation on E02. The next external case
search should prioritise a real user-visible loss, not schema duplication
alone. B0 remains default and X6 sealed.
