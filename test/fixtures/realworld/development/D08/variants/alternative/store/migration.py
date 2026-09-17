class MigrationInterrupted(RuntimeError):
    pass


def domain_from_email(email):
    parts = email.rsplit("@", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"invalid email address: {email!r}")
    return parts[1].casefold()


TRIGGER = """
CREATE TRIGGER accounts_fill_email_domain
AFTER INSERT ON accounts
WHEN NEW.email_domain IS NULL OR NEW.email_domain = ''
BEGIN
  UPDATE accounts
  SET email_domain = lower(substr(NEW.email, instr(NEW.email, '@') + 1))
  WHERE id = NEW.id;
END
"""


def _table_info(connection):
    return list(connection.execute("PRAGMA table_info(accounts)"))


def _replace_trigger(connection):
    connection.execute("DROP TRIGGER IF EXISTS accounts_fill_email_domain")
    connection.execute(TRIGGER)


def migrate(connection, *, batch_size=100, interrupt_after_batches=None,
            derive=domain_from_email):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    info = _table_info(connection)
    with connection:
        if not any(row[1] == "email_domain" for row in info):
            connection.execute("ALTER TABLE accounts ADD COLUMN email_domain TEXT")
        _replace_trigger(connection)

    completed_batches = 0
    while True:
        pending = connection.execute(
            """
            SELECT id, email FROM accounts
            WHERE coalesce(email_domain, '') = ''
            ORDER BY id LIMIT ?
            """,
            (batch_size,),
        ).fetchall()
        if not pending:
            break
        values = [(derive(email), account_id) for account_id, email in pending]
        with connection:
            connection.executemany(
                "UPDATE accounts SET email_domain = ? WHERE id = ?", values
            )
        completed_batches += 1
        if (interrupt_after_batches is not None
                and completed_batches == interrupt_after_batches):
            raise MigrationInterrupted("simulated stop after durable batch")

    info = _table_info(connection)
    email_domain = next(row for row in info if row[1] == "email_domain")
    if email_domain[3] == 0:
        with connection:
            connection.execute("DROP TRIGGER IF EXISTS accounts_fill_email_domain")
            connection.execute(
                """
                CREATE TABLE replacement_accounts(
                  id INTEGER PRIMARY KEY,
                  email TEXT NOT NULL,
                  email_domain TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                INSERT INTO replacement_accounts(id, email, email_domain)
                SELECT id, email, email_domain FROM accounts
                """
            )
            connection.execute("DROP TABLE accounts")
            connection.execute(
                "ALTER TABLE replacement_accounts RENAME TO accounts"
            )
            _replace_trigger(connection)
            connection.execute("PRAGMA user_version = 2")
    else:
        with connection:
            _replace_trigger(connection)
            connection.execute("PRAGMA user_version = 2")
