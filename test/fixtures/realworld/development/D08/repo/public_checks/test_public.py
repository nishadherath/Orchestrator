import sqlite3
import unittest

from store.legacy import insert_account
from store.migration import MigrationInterrupted, migrate


def database():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE accounts(id INTEGER PRIMARY KEY, email TEXT NOT NULL)"
    )
    connection.execute("PRAGMA user_version = 1")
    connection.executemany(
        "INSERT INTO accounts(id, email) VALUES (?, ?)",
        [(7, "Ada@Example.COM"), (19, "lin@service.test")],
    )
    connection.commit()
    return connection


class PublicMigrationTests(unittest.TestCase):
    def test_interrupted_migration_resumes_and_keeps_legacy_writer(self):
        connection = database()
        with self.assertRaises(MigrationInterrupted):
            migrate(connection, batch_size=1, interrupt_after_batches=1)

        first_domain = connection.execute(
            "SELECT email_domain FROM accounts WHERE id = 7"
        ).fetchone()[0]
        self.assertEqual(first_domain, "example.com")

        insert_account(connection, 41, "new@during.test")
        migrate(connection, batch_size=1)
        migrate(connection, batch_size=1)

        rows = connection.execute(
            "SELECT id, email, email_domain FROM accounts ORDER BY id"
        ).fetchall()
        self.assertEqual(rows, [
            (7, "Ada@Example.COM", "example.com"),
            (19, "lin@service.test", "service.test"),
            (41, "new@during.test", "during.test"),
        ])
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(accounts)")}
        self.assertEqual(columns["email_domain"][3], 1)
        insert_account(connection, 83, "old@after.test")
        self.assertEqual(
            connection.execute(
                "SELECT email_domain FROM accounts WHERE id = 83"
            ).fetchone()[0],
            "after.test",
        )


if __name__ == "__main__":
    unittest.main()
