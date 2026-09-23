class MigrationInterrupted(RuntimeError):
    pass


def domain_from_email(email):
    return email.rsplit("@", 1)[1].lower()


def migrate(connection, *, batch_size=100, interrupt_after_batches=None,
            derive=domain_from_email):
    del batch_size, interrupt_after_batches
    columns = {row[1] for row in connection.execute("PRAGMA table_info(accounts)")}
    with connection:
        if "email_domain" not in columns:
            connection.execute("ALTER TABLE accounts ADD COLUMN email_domain TEXT")
        rows = connection.execute("SELECT id, email FROM accounts").fetchall()
        for account_id, email in rows:
            connection.execute(
                "UPDATE accounts SET email_domain = ? WHERE id = ?",
                (derive(email), account_id),
            )
        connection.execute("PRAGMA user_version = 2")
