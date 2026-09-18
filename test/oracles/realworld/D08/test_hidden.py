import os
import sqlite3
import sys
import unittest
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from store.legacy import insert_account
from store.migration import MigrationInterrupted, migrate


def make_database(rows):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE accounts(id INTEGER PRIMARY KEY, email TEXT NOT NULL)"
    )
    connection.execute("PRAGMA user_version = 1")
    connection.executemany(
        "INSERT INTO accounts(id, email) VALUES (?, ?)", rows
    )
    connection.commit()
    return connection


class HiddenMigrationTests(unittest.TestCase):
    def test_resume_preserves_data_and_supports_legacy_writes(self):
        initial = [
            (10, "one@Alpha.TEST"),
            (40, "two@beta.example"),
            (90, "three@gamma.internal"),
        ]
        connection = make_database(initial)
        with self.assertRaises(MigrationInterrupted):
            migrate(connection, batch_size=2, interrupt_after_batches=1)

        durable = connection.execute(
            "SELECT id, email_domain FROM accounts ORDER BY id"
        ).fetchall()
        self.assertEqual(durable[:2], [(10, "alpha.test"), (40, "beta.example")])
        self.assertIsNone(durable[2][1])

        insert_account(connection, 125, "legacy@rolling.test")
        migrate(connection, batch_size=2)
        expected = initial + [(125, "legacy@rolling.test")]
        actual = connection.execute(
            "SELECT id, email FROM accounts ORDER BY id"
        ).fetchall()
        self.assertEqual(actual, expected)
        domains = dict(connection.execute(
            "SELECT id, email_domain FROM accounts"
        ))
        self.assertEqual(domains, {
            10: "alpha.test",
            40: "beta.example",
            90: "gamma.internal",
            125: "rolling.test",
        })
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(accounts)")}
        self.assertEqual(columns["email_domain"][3], 1)
        self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)

        insert_account(connection, 301, "old-reader@final.test")
        self.assertEqual(
            connection.execute(
                "SELECT email_domain FROM accounts WHERE id = 301"
            ).fetchone()[0],
            "final.test",
        )
        before = connection.execute(
            "SELECT id, email, email_domain FROM accounts ORDER BY id"
        ).fetchall()
        migrate(connection, batch_size=1)
        self.assertEqual(
            connection.execute(
                "SELECT id, email, email_domain FROM accounts ORDER BY id"
            ).fetchall(),
            before,
        )

    def test_failed_batch_rolls_back_and_can_retry(self):
        connection = make_database([
            (5, "first@one.test"),
            (6, "second@two.test"),
        ])
        calls = 0

        def fail_second(email):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("derived value unavailable")
            return email.rsplit("@", 1)[1]

        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            migrate(connection, batch_size=2, derive=fail_second)
        self.assertEqual(
            connection.execute(
                "SELECT email_domain FROM accounts ORDER BY id"
            ).fetchall(),
            [(None,), (None,)],
        )
        migrate(connection, batch_size=2)
        self.assertEqual(
            connection.execute(
                "SELECT email_domain FROM accounts ORDER BY id"
            ).fetchall(),
            [("one.test",), ("two.test",)],
        )


if __name__ == "__main__":
    unittest.main()
