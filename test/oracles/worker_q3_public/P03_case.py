"""Hidden, provider-free command and option diagnostic cases for Click."""
import json
import sys

import click
from click.testing import CliRunner


def group(*names):
    @click.group()
    def cli():
        pass

    for name in names:
        @cli.command(name=name)
        def command():
            click.echo("ran")
    return cli


def run(case):
    runner = CliRunner()
    if case == "single-command-suggestion":
        result = runner.invoke(group("push", "status"), ["pusg"])
        return result.exit_code != 0 and "Did you mean 'push'?" in result.output
    if case == "multiple-command-suggestions":
        result = runner.invoke(group("declare", "refine", "deploy"), ["decline"])
        return (result.exit_code != 0
                and "Did you mean one of: 'declare', 'refine'?" in result.output)
    if case in {"single-option-suggestion", "multiple-option-suggestions"}:
        @click.command()
        @click.option("--bound")
        @click.option("--count")
        def cli(bound, count):
            click.echo(f"{bound}:{count}")

        if case == "single-option-suggestion":
            result = runner.invoke(cli, ["--cat"])
            return (result.exit_code != 0
                    and "Did you mean '--count'?" in result.output)
        result = runner.invoke(cli, ["--bounds"])
        return (result.exit_code != 0
                and "Did you mean one of: '--bound', '--count'?" in result.output)
    if case == "unrelated-command":
        result = runner.invoke(group("push", "status"), ["quartz"])
        return (result.exit_code != 0
                and "No such command 'quartz'." in result.output
                and "Did you mean" not in result.output)
    if case == "exception-contract":
        if not hasattr(click, "NoSuchCommand"):
            return False
        error = click.NoSuchCommand("pusg", possibilities=["push"])
        return (isinstance(error, click.UsageError)
                and error.command_name == "pusg"
                and "Did you mean 'push'?" in error.format_message())
    raise ValueError("unknown hidden case")


if __name__ == "__main__":
    case_name = json.load(sys.stdin)["case"]
    print(json.dumps({"ok": run(case_name)}, sort_keys=True))
