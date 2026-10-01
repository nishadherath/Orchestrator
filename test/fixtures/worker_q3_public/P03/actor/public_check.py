"""Public smoke checks for consistent Click typo diagnostics."""
import unittest

import click
from click.testing import CliRunner


class DiagnosticTests(unittest.TestCase):
    def test_nearby_subcommand_is_suggested(self):
        @click.group()
        def cli():
            pass

        @cli.command()
        def push():
            pass

        result = CliRunner().invoke(cli, ["pause"])
        self.assertNotEqual(0, result.exit_code)
        self.assertIn("No such command 'pause'.", result.output)
        self.assertIn("Did you mean 'push'?", result.output)

    def test_nearby_option_uses_the_same_suggestion_style(self):
        @click.command()
        @click.option("--count", type=int)
        def cli(count):
            click.echo(count)

        result = CliRunner().invoke(cli, ["--cat"])
        self.assertNotEqual(0, result.exit_code)
        self.assertIn("No such option '--cat'.", result.output)
        self.assertIn("Did you mean '--count'?", result.output)

    def test_valid_command_still_runs(self):
        @click.command()
        def cli():
            click.echo("ready")

        result = CliRunner().invoke(cli, [])
        self.assertEqual(0, result.exit_code)
        self.assertEqual("ready\n", result.output)


if __name__ == "__main__":
    unittest.main()
