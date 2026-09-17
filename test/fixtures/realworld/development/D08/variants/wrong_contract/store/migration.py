class MigrationInterrupted(RuntimeError):
    pass


def domain_from_email(email):
    return email.rsplit("@", 1)[1].lower()


def migrate(connection, *, batch_size=100, interrupt_after_batches=None,
            derive=domain_from_email):
    del batch_size, interrupt_after_batches
    rows = connection.execute("SELECT email FROM accounts ORDER BY id").fetchall()
    with connection:
        connection.execute(
            """
            CREATE TABLE replacement_accounts(
              id INTEGER PRIMARY KEY,
              email TEXT NOT NULL,
              email_domain TEXT NOT NULL
            )
            """
        )
        for (email,) in rows:
            connection.execute(
                "INSERT INTO replacement_accounts(email, email_domain) VALUES (?, ?)",
                (email, derive(email)),
            )
        connection.execute("DROP TABLE accounts")
        connection.execute("ALTER TABLE replacement_accounts RENAME TO accounts")
        connection.execute("PRAGMA user_version = 2")
