class MigrationInterrupted(RuntimeError):
    pass


def domain_from_email(email):
    return email.rsplit("@", 1)[1].lower()


def migrate(connection, *, batch_size=100, interrupt_after_batches=None,
            derive=domain_from_email):
    """Apply the version-two schema in one step."""
    del batch_size, interrupt_after_batches, derive
    with connection:
        connection.execute(
            "ALTER TABLE accounts ADD COLUMN email_domain TEXT NOT NULL"
        )
        connection.execute("PRAGMA user_version = 2")
