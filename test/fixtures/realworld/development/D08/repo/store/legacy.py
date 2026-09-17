def insert_account(connection, account_id, email):
    """Write through the version-one interface used during rolling deploys."""
    with connection:
        connection.execute(
            "INSERT INTO accounts(id, email) VALUES (?, ?)",
            (account_id, email),
        )
