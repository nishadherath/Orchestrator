"""Protected behavioural checks for the attrs F01 development case.

Run only against an isolated actor copy by setting X5_F01_ACTOR_ROOT.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


actor = Path(os.environ["X5_F01_ACTOR_ROOT"])
if actor.is_symlink() or not actor.is_dir():
    raise RuntimeError("candidate actor is unavailable")
sys.path.insert(0, str(actor))
import attr  # noqa: E402


def inherited_aliases() -> None:
    seen = []

    @attr.s(auto_attribs=True)
    class Base:
        _base: str

    def record(cls, fields):
        seen.extend((field.name, field.alias, field.alias_is_default)
                    for field in fields)
        return fields

    @attr.s(auto_attribs=True, field_transformer=record)
    class Child(Base):
        _child: str

    assert ("_base", "base", True) in seen
    assert ("_child", "child", True) in seen
    item = Child(base="a", child="b")
    assert (item._base, item._child) == ("a", "b")


def generator_transformer() -> None:
    seen = []

    def transform(cls, fields):
        seen.extend((field.name, field.alias) for field in fields)
        return (field for field in fields)

    @attr.define(field_transformer=transform)
    class Item:
        _token: str

    assert seen == [("_token", "token")]
    assert Item(token="value")._token == "value"


def nested_validation_suppression() -> None:
    @attr.s
    class Item:
        value = attr.ib(validator=attr.validators.instance_of(int))

    try:
        with attr.validators.disabled():
            with attr.validators.disabled():
                Item("wrong")
            Item("still disabled")
        try:
            Item("must fail")
        except TypeError:
            pass
        else:
            raise AssertionError("validation stayed disabled after outer exit")
    finally:
        attr.validators.set_disabled(False)


def prior_state_survives_exception() -> None:
    attr.validators.set_disabled(True)
    try:
        try:
            with attr.validators.disabled():
                raise RuntimeError("exit through exception")
        except RuntimeError:
            pass
        assert attr.validators.get_disabled() is True
    finally:
        attr.validators.set_disabled(False)


def explicit_alias_still_works() -> None:
    @attr.define
    class Item:
        _token: str = attr.field(alias="key")

    metadata = attr.fields(Item)[0]
    assert metadata.alias == "key"
    assert metadata.alias_is_default is False
    assert Item(key="secret")._token == "secret"


def ordinary_validation_still_runs() -> None:
    @attr.s
    class Item:
        value = attr.ib(validator=attr.validators.instance_of(int))

    assert Item(3).value == 3
    try:
        Item("wrong")
    except TypeError:
        pass
    else:
        raise AssertionError("ordinary validator did not run")


CASES = (
    ("inherited_aliases", inherited_aliases, True),
    ("generator_transformer", generator_transformer, True),
    ("nested_validation_suppression", nested_validation_suppression, True),
    ("prior_state_survives_exception", prior_state_survives_exception, True),
    ("explicit_alias_still_works", explicit_alias_still_works, False),
    ("ordinary_validation_still_runs", ordinary_validation_still_runs, False),
)


def main() -> None:
    results = []
    for name, check, critical in CASES:
        try:
            check()
            passed = True
        except Exception:
            passed = False
        results.append({"name": name, "passed": passed, "critical": critical,
                        "weight": 1})
    print(json.dumps({"schema_version": 1, "cases": results}, sort_keys=True))
    if not all(row["passed"] for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
