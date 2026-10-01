"""Small SQLite reproduction of Alembic issue 1768 on its reported versions."""

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Boolean, Column, Integer, MetaData, Table, create_engine
from sqlalchemy.exc import IntegrityError


NAMING = {"ck": "ck_%(table_name)s_%(constraint_name)s"}
metadata = MetaData(naming_convention=NAMING)
Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
)
engine = create_engine("sqlite://")
metadata.create_all(engine)

direct_metadata = MetaData(naming_convention=NAMING)
Table(
    "direct_user",
    direct_metadata,
    Column("id", Integer, primary_key=True),
    Column("is_active", Boolean(create_constraint=True, name="is_active")),
)
direct_engine = create_engine("sqlite://")
direct_metadata.create_all(direct_engine)
with direct_engine.connect() as connection:
    direct = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='direct_user'"
    ).scalar_one()

with engine.begin() as connection:
    before = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='user'"
    ).scalar_one()
    operations = Operations(MigrationContext.configure(connection))
    with operations.batch_alter_table(
        "user", naming_convention=NAMING, recreate="always"
    ) as batch:
        batch.add_column(
            Column("is_active", Boolean(create_constraint=True, name="is_active"))
        )
    after = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='user'"
    ).scalar_one()
    check = "CHECK (is_active IN (0, 1))"
    assert direct.count(check) == 1, direct
    assert before.count(check) == 0, before
    assert after.count(check) == 2, after
    try:
        connection.exec_driver_sql("INSERT INTO user (id, is_active) VALUES (1, 2)")
    except IntegrityError:
        invalid_value_rejected = True
    else:
        invalid_value_rejected = False
    assert invalid_value_rejected, after
    print("DIRECT_CHECK_COUNT:", direct.count(check))
    print("BEFORE_CHECK_COUNT:", before.count(check))
    print("AFTER_CHECK_COUNT:", after.count(check))
    print("INVALID_VALUE_REJECTED:", invalid_value_rejected)
    print("DIRECT:\n", direct)
    print("BEFORE:\n", before)
    print("AFTER:\n", after)
