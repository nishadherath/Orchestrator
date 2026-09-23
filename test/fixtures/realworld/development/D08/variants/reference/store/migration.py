class MigrationInterrupted(RuntimeError):
    pass


def domain_from_email(email):
    local, separator, domain = email.rpartition("@")
    if not local or not separator or not domain:
        raise ValueError(f"invalid email address: {email!r}")
    return domain.lower()


def _columns(connection):
    return {row[1]: row for row in connection.execute("PRAGMA table_info(accounts)")}


def _install_legacy_trigger(connection):
    connection.execute("DROP TRIGGER IF EXISTS accounts_fill_email_domain")
    connection.execute(
        """
        CREATE TRIGGER accounts_fill_email_domain
        AFTER INSERT ON accounts
        WHEN NEW.email_domain IS NULL OR NEW.email_domain = ''
        BEGIN
          UPDATE accounts
          SET email_domain = lower(substr(NEW.email, instr(NEW.email, '@') + 1))
          WHERE id = NEW.id;
        END
        """
    )


def _prepare_transition(connection):
    with connection:
        if "email_domain" not in _columns(connection):
            connection.execute("ALTER TABLE accounts ADD COLUMN email_domain TEXT")
        _install_legacy_trigger(connection)


def _backfill(connection, batch_size, interrupt_after_batches, derive):
    batches = 0
    while True:
        rows = connection.execute(
            """
            SELECT id, email FROM accounts
            WHERE email_domain IS NULL OR email_domain = ''
            ORDER BY id LIMIT ?
            """,
            (batch_size,),
        ).fetchall()
        if not rows:
            return
        with connection:
            for account_id, email in rows:
                connection.execute(
                    "UPDATE accounts SET email_domain = ? WHERE id = ?",
                    (derive(email), account_id),
                )
        batches += 1
        if interrupt_after_batches is not None and batches >= interrupt_after_batches:
            raise MigrationInterrupted("simulated stop after durable batch")


def _finalise(connection):
    if _columns(connection)["email_domain"][3] == 1:
        with connection:
            _install_legacy_trigger(connection)
            connection.execute("PRAGMA user_version = 2")
        return

    with connection:
        connection.execute("DROP TRIGGER IF EXISTS accounts_fill_email_domain")
        connection.execute("DROP TABLE IF EXISTS accounts_v2")
        connection.execute(
            """
            CREATE TABLE accounts_v2(
              id INTEGER PRIMARY KEY,
              email TEXT NOT NULL,
              email_domain TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            INSERT INTO accounts_v2(id, email, email_domain)
            SELECT id, email, email_domain FROM accounts
            """
        )
        connection.execute("DROP TABLE accounts")
        connection.execute("ALTER TABLE accounts_v2 RENAME TO accounts")
        _install_legacy_trigger(connection)
        connection.execute("PRAGMA user_version = 2")


def migrate(connection, *, batch_size=100, interrupt_after_batches=None,
            derive=domain_from_email):
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    _prepare_transition(connection)
    _backfill(connection, batch_size, interrupt_after_batches, derive)
    _finalise(connection)
