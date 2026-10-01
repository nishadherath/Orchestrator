"""Independent pickle and legacy-state probes."""
import json
import pickle
import sys

from packaging._parser import Op, Value, Variable
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet


def run(row):
    kind = row["kind"]
    try:
        if kind == "node":
            node = Variable("python_version")
            return pickle.loads(pickle.dumps(node)).value
        if kind == "marker":
            marker = Marker(row["text"])
            loaded = pickle.loads(pickle.dumps(marker))
            return [str(loaded), loaded == marker]
        if kind == "requirement":
            requirement = Requirement(row["text"])
            loaded = pickle.loads(pickle.dumps(requirement))
            return [str(loaded), loaded == requirement]
        if kind == "node-legacy":
            node = Value.__new__(Value)
            node.__setstate__((None, {"value": "3.8"}))
            return node.value
        if kind == "marker-legacy":
            marker = Marker.__new__(Marker)
            marker.__setstate__((None, {"_markers": [(Variable("python_version"), Op(">="), Value("3.8"))]}))
            return str(marker)
        if kind == "requirement-legacy":
            requirement = Requirement.__new__(Requirement)
            requirement.__setstate__({"name": "sample", "extras": set(),
                                      "specifier": SpecifierSet(">=2"),
                                      "url": None, "marker": None})
            return str(requirement)
        if kind == "invalid-requirement":
            requirement = Requirement.__new__(Requirement)
            requirement.__setstate__(42)
            return "accepted-invalid"
        if kind == "invalid-node":
            node = Op.__new__(Op)
            node.__setstate__({"value": 123})
            return "accepted-invalid"
        if kind == "invalid-marker":
            marker = Marker.__new__(Marker)
            marker.__setstate__("not valid marker text")
            return "accepted-invalid"
        if kind == "control":
            return str(Requirement("sample>=2"))
    except Exception as exc:
        return type(exc).__name__
    raise ValueError(kind)


print(json.dumps(run(json.loads(sys.stdin.read())), sort_keys=True))
