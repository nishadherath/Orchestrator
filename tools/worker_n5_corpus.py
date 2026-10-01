#!/usr/bin/env python3
"""Generate the frozen, task-sensitive N5/N6 worker corpus.

The development and reserved sets have the same six work families and four
routine, moderate and complex tasks each. Every task has two public examples
and three independent hidden cases. The reference implementation is used only
to derive expected data and is never copied into an actor package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "test" / "fixtures" / "worker_n5_realworld"

REFERENCE = '''import json, sys

def solve(d):
    kind = d["kind"]
    if kind == "config_precedence":
        for source in ("environment", "file", "defaults"):
            value = d[source].get(d["key"])
            if value is not None:
                return {"value": value, "source": source}
        return {"value": None, "source": "missing"}
    if kind == "retry_decision":
        retry = d["status"] in (408, 429, 500, 502, 503, 504) and d["attempt"] < d["max_attempts"]
        return {"retry": retry, "delay_ms": min(d["base_ms"] * (2 ** (d["attempt"] - 1)), d["cap_ms"]) if retry else 0}
    if kind == "deduplicate":
        seen, output = set(), []
        for row in d["records"]:
            key = str(row.get("id", "")).strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append({"id": key, "value": row.get("value")})
        return output
    if kind == "optimistic_write":
        if d["expected_version"] != d["current_version"]:
            return {"applied": False, "version": d["current_version"], "value": d["current_value"]}
        return {"applied": True, "version": d["current_version"] + 1, "value": d["new_value"]}
    if kind == "page_merge":
        seen, rows = set(), []
        for page in d["pages"]:
            for row in page:
                if row["id"] not in seen:
                    seen.add(row["id"])
                    rows.append(row)
        start, limit = d["offset"], d["limit"]
        return {"items": rows[start:start + limit], "next_offset": start + limit if start + limit < len(rows) else None}
    if kind == "incident_triage":
        bad = [name for name in d["required"] if d["checks"].get(name) != "ok"]
        unknown = [name for name in bad if name not in d["checks"]]
        return {"status": "blocked" if unknown else "degraded" if bad else "healthy", "failing": bad, "missing_evidence": unknown}
    if kind == "feature_gate":
        if d["account"] in d["denied"]:
            return {"enabled": False, "reason": "denied"}
        if not d["flag"] or any(not d["prerequisites"].get(k, False) for k in d["requires"]):
            return {"enabled": False, "reason": "prerequisite"}
        return {"enabled": d["account"] in d["allowed"], "reason": "allowed" if d["account"] in d["allowed"] else "not-listed"}
    if kind == "message_delivery":
        seen, delivered, retry, dead = set(d["already_delivered"]), [], [], []
        for row in d["messages"]:
            key = row["id"]
            if key in seen:
                continue
            seen.add(key)
            if row["outcome"] == "ok":
                delivered.append(key)
            elif row["attempt"] < d["retry_limit"]:
                retry.append(key)
            else:
                dead.append(key)
        return {"delivered": delivered, "retry": retry, "dead_letter": dead}
    if kind == "inventory_reconcile":
        stock, rejected = dict(d["opening"]), []
        for index, event in enumerate(d["events"]):
            sku, delta = event["sku"], event["delta"]
            if sku not in stock or stock[sku] + delta < 0:
                rejected.append(index)
            else:
                stock[sku] += delta
        return {"stock": stock, "rejected": rejected}
    if kind == "lease_fencing":
        owner, expiry, fence = d["owner"], d["expiry"], d["fence"]
        results = []
        for event in d["requests"]:
            if owner is None or event["at"] >= expiry or owner == event["owner"]:
                if owner != event["owner"] or event["at"] >= expiry:
                    fence += 1
                owner, expiry = event["owner"], event["at"] + event["ttl"]
                results.append({"granted": True, "fence": fence})
            else:
                results.append({"granted": False, "fence": fence})
        return {"owner": owner, "expiry": expiry, "fence": fence, "results": results}
    if kind == "token_bucket":
        tokens, last, decisions = d["capacity"], d["start"], []
        for request in d["requests"]:
            now = request["at"]
            tokens = min(d["capacity"], tokens + max(0, now - last) * d["refill_per_second"])
            last = max(last, now)
            allowed = tokens >= request["cost"]
            if allowed:
                tokens -= request["cost"]
            decisions.append(allowed)
        return {"allowed": decisions, "remaining": tokens}
    if kind == "dependency_diagnosis":
        nodes, depends = d["status"], d["depends_on"]
        failed = {name for name, status in nodes.items() if status != "ok"}
        roots = sorted(name for name in failed if not any(dep in failed for dep in depends.get(name, [])))
        blocked = sorted(name for name in failed if name not in roots)
        return {"root_failures": roots, "downstream": blocked, "complete": not failed}
    raise ValueError("unknown task kind")

if __name__ == "__main__":
    print(json.dumps(solve(json.loads(sys.stdin.readline()))))
'''

scope: dict = {}
exec(REFERENCE, scope)
reference_solve = scope["solve"]

# The inputs are data, not answer keys. Five distinct cases per split keep the
# public example from revealing the hidden cases or the reference algorithm.
SPECS = [
    ("configuration", "routine", "config_precedence",
     "Resolve one configuration key from environment, file and defaults in that order. Null means absent. Return its value and source, or null and missing.",
     [{"key": k, "environment": e, "file": f, "defaults": z} for k, e, f, z in [
         ("port", {"port": 8080}, {"port": 80}, {"port": 40}), ("port", {}, {"port": 80}, {"port": 40}),
         ("mode", {"mode": None}, {}, {"mode": "safe"}), ("x", {}, {}, {}), ("x", {"x": False}, {"x": True}, {}),
         ("timeout", {"timeout": 0}, {}, {"timeout": 10}), ("timeout", {}, {"timeout": None}, {"timeout": 10}),
         ("region", {}, {}, {"region": "ap"}), ("region", {"region": "eu"}, {}, {}), ("x", {}, {"x": ""}, {})]]),
    ("resilience", "routine", "retry_decision",
     "For HTTP status, attempt number and retry limit, retry only 408, 429 or 5xx transient statuses. Back off exponentially from base_ms, capped at cap_ms; return zero delay when not retrying.",
     [{"status": s, "attempt": a, "max_attempts": m, "base_ms": b, "cap_ms": c} for s, a, m, b, c in [
         (503,1,3,100,1000),(200,1,3,100,1000),(429,2,3,50,75),(500,3,3,100,800),(404,1,4,20,100),
         (408,1,2,10,100),(502,2,4,25,60),(504,5,5,30,1000),(201,1,2,40,100),(503,4,6,10,50)]]),
    ("integrity", "routine", "deduplicate",
     "Normalise record IDs by trimming whitespace and lowercasing. Drop blank IDs and later duplicates while retaining the first value and input order. Return normalised records.",
     [{"records": rows} for rows in [
         [{"id":" A ","value":1},{"id":"a","value":2}],[],[{"id":" ","value":1},{"id":"b","value":2}],
         [{"id":"X","value":0},{"id":"x","value":9},{"id":"Y","value":3}], [{"value":1}],
         [{"id":"P","value":False},{"id":"Q","value":None}], [{"id":"  ","value":1}],
         [{"id":"z","value":1},{"id":"Z ","value":3}], [{"id":"abc","value":[]}],
         [{"id":" a","value":4},{"id":"b ","value":5},{"id":" A ","value":6}]]]),
    ("concurrency", "routine", "optimistic_write",
     "Apply a write only when expected_version matches current_version. Return applied, resulting version and value; a conflict preserves the current state.",
     [{"expected_version":e,"current_version":c,"current_value":v,"new_value":n} for e,c,v,n in [
         (1,1,"old","new"),(1,2,"old","new"),(0,0,None,"x"),(4,4,False,True),(2,1,5,6),
         (8,8,{"x":1},{"x":2}),(7,9,[],[1]),(3,3,"a",None),(5,6,0,1),(10,10,10,11)]]),
    ("protocol", "moderate", "page_merge",
     "Combine ordered API pages, keeping the first record for each ID. Apply zero-based offset and limit after deduplication. Return items and the next offset, or null at the end.",
     [{"pages":p,"offset":o,"limit":l} for p,o,l in [
         ([[{"id":"a"},{"id":"b"}],[{"id":"b"},{"id":"c"}]],0,2), ([],0,3),
         ([[{"id":1,"v":1}],[{"id":1,"v":2},{"id":2,"v":3}]],1,2),
         ([[{"id":"x"},{"id":"y"},{"id":"z"}]],2,1), ([[{"id":"a"}]],2,2),
         ([[{"id":"r"}],[{"id":"s"},{"id":"t"}]],0,1), ([[{"id":1}],[{"id":2}]],1,1),
         ([[{"id":"k"},{"id":"k"}]],0,5), ([[],[{"id":"q"}]],0,3),
         ([[{"id":"m"},{"id":"n"}],[{"id":"m"},{"id":"p"}]],1,2)]]),
    ("diagnosis", "moderate", "incident_triage",
     "Triage required health checks in their declared order. Missing evidence is blocked; failing observed checks are degraded; all OK is healthy. Return failing names and missing-evidence names.",
     [{"required":r,"checks":c} for r,c in [
         (["db","api"],{"db":"ok","api":"fail"}), (["db"],{}), ([],{}),
         (["a","b"],{"a":"ok","b":"ok"}), (["a","b"],{"a":"fail"}),
         (["cache","db"],{"cache":"slow","db":"ok"}), (["x","y"],{"x":"bad","y":"bad"}),
         (["api"],{"api":"ok","extra":"bad"}), (["a","b","c"],{"a":"ok","c":"bad"}),
         (["service","queue"],{"queue":"ok"})]]),
    ("configuration", "moderate", "feature_gate",
     "Deny-listed accounts take precedence. Otherwise the flag and every named prerequisite must be true. Then enable only allow-listed accounts; return a reason of denied, prerequisite, allowed or not-listed.",
     [{"account":a,"denied":dn,"allowed":al,"flag":fl,"requires":rq,"prerequisites":pr} for a,dn,al,fl,rq,pr in [
         ("a",[],["a"],True,["paid"],{"paid":True}),("a",["a"],["a"],True,[],{}),
         ("b",[],["a"],True,[],{}),("a",[],["a"],False,[],{}),("a",[],["a"],True,["x"],{}),
         ("c",[],["c"],True,["x","y"],{"x":True,"y":False}),
         ("c",[],["c"],True,["x","y"],{"x":True,"y":True}),
         ("d",["d"],[],False,["x"],{}),("e",[],[],True,[],{}),("f",[],["f"],True,["p"],{"p":False})]]),
    ("resilience", "moderate", "message_delivery",
     "Process ordered message attempts idempotently, ignoring previously delivered IDs and duplicate IDs in this batch. Successful attempts are delivered; failed attempts below retry_limit retry; others go to dead_letter.",
     [{"already_delivered":old,"retry_limit":lim,"messages":msg} for old,lim,msg in [
         ([],3,[{"id":"a","outcome":"ok","attempt":1}]),
         (["a"],3,[{"id":"a","outcome":"fail","attempt":3}]),
         ([],3,[{"id":"a","outcome":"fail","attempt":2}]),
         ([],3,[{"id":"a","outcome":"fail","attempt":3}]),
         ([],2,[{"id":"x","outcome":"ok","attempt":1},{"id":"x","outcome":"fail","attempt":2}]),
         (["z"],2,[{"id":"z","outcome":"ok","attempt":1},{"id":"y","outcome":"fail","attempt":1}]),
         ([],1,[{"id":"a","outcome":"fail","attempt":1},{"id":"b","outcome":"ok","attempt":1}]),
         ([],4,[]), ([],2,[{"id":"m","outcome":"fail","attempt":1},{"id":"n","outcome":"ok","attempt":2}]),
         ([],2,[{"id":"m","outcome":"ok","attempt":1},{"id":"n","outcome":"fail","attempt":2}])]]),
    ("integrity", "complex", "inventory_reconcile",
     "Reconcile ordered stock deltas. Reject an event by its zero-based position if its SKU is unknown or it would make stock negative. A rejected event must not change later calculations.",
     [{"opening":o,"events":e} for o,e in [
         ({"a":2},[{"sku":"a","delta":-1}]), ({"a":1},[{"sku":"a","delta":-2},{"sku":"a","delta":-1}]),
         ({"a":1},[{"sku":"b","delta":1}]), ({"a":0},[{"sku":"a","delta":0},{"sku":"a","delta":2}]),
         ({"x":3,"y":1},[{"sku":"x","delta":-4},{"sku":"y","delta":-1},{"sku":"x","delta":-3}]),
         ({"x":1},[{"sku":"x","delta":-2},{"sku":"x","delta":-1},{"sku":"x","delta":1}]),
         ({"p":2},[]), ({"p":2},[{"sku":"p","delta":-2},{"sku":"p","delta":-1}]),
         ({"p":3,"q":0},[{"sku":"q","delta":-1},{"sku":"p","delta":-2},{"sku":"q","delta":2}]),
         ({"a":4},[{"sku":"a","delta":-3},{"sku":"a","delta":-2},{"sku":"a","delta":1}])]]),
    ("concurrency", "complex", "lease_fencing",
     "Apply lease requests in order. Grant if unowned, expired at request time, or the same owner renews. A new owner or an expired reacquisition increments the fencing token. Return each grant decision and final lease state.",
     [{"owner":o,"expiry":e,"fence":f,"requests":q} for o,e,f,q in [
         (None,0,0,[{"owner":"a","at":1,"ttl":5}]),
         ("a",10,2,[{"owner":"b","at":9,"ttl":4}]),
         ("a",10,2,[{"owner":"b","at":10,"ttl":4}]),
         ("a",10,2,[{"owner":"a","at":5,"ttl":8}]),
         ("a",10,2,[{"owner":"b","at":9,"ttl":2},{"owner":"b","at":10,"ttl":2}]),
         (None,0,3,[{"owner":"x","at":2,"ttl":3},{"owner":"y","at":5,"ttl":3}]),
         ("x",3,4,[]), ("x",3,4,[{"owner":"x","at":3,"ttl":2}]),
         ("x",10,4,[{"owner":"x","at":2,"ttl":4},{"owner":"y","at":6,"ttl":2}]),
         ("a",4,1,[{"owner":"b","at":5,"ttl":2},{"owner":"a","at":6,"ttl":2}])]]),
    ("protocol", "complex", "token_bucket",
     "Evaluate ordered requests using a token bucket. Start full at start, refill per elapsed second up to capacity, never rewind time for out-of-order timestamps, and spend tokens only for admitted requests.",
     [{"capacity":c,"start":s,"refill_per_second":r,"requests":q} for c,s,r,q in [
         (3,0,1,[{"at":0,"cost":2},{"at":0,"cost":2}]),
         (3,0,1,[{"at":1,"cost":3},{"at":2,"cost":1}]),
         (5,0,2,[{"at":0,"cost":5},{"at":1,"cost":3}]),
         (2,0,1,[]), (2,0,1,[{"at":5,"cost":1}]),
         (4,0,1,[{"at":2,"cost":3},{"at":1,"cost":2}]),
         (1,0,1,[{"at":0,"cost":2},{"at":1,"cost":1}]),
         (5,5,2,[{"at":5,"cost":4},{"at":7,"cost":5}]),
         (3,0,0,[{"at":10,"cost":2},{"at":20,"cost":2}]),
         (4,0,1,[{"at":0,"cost":1},{"at":1,"cost":4},{"at":2,"cost":3}])]]),
    ("diagnosis", "complex", "dependency_diagnosis",
     "From service status and dependency edges, identify failed services with no failed direct dependency as root failures. Other failed services are downstream. Sort both lists and mark complete only when none failed.",
     [{"status":st,"depends_on":dp} for st,dp in [
         ({"db":"bad","api":"bad"},{"api":["db"]}),
         ({"db":"ok","api":"bad"},{"api":["db"]}),
         ({"db":"ok","api":"ok"},{"api":["db"]}),
         ({"a":"bad","b":"bad","c":"bad"},{"c":["a","b"]}),
         ({"a":"bad","b":"bad","c":"bad"},{"a":[],"b":["a"],"c":["b"]}),
         ({"a":"ok","b":"bad","c":"bad"},{"b":["a"],"c":["b"]}),
         ({"x":"bad"},{}), ({"x":"bad","y":"bad"},{"x":[],"y":[]}),
         ({"x":"ok","y":"ok"},{"y":["x"]}),
         ({"db":"bad","cache":"bad","api":"bad"},{"api":["db","cache"]})]])
]


def planned_files() -> dict[str, str]:
    output: dict[str, str] = {}
    catalogue = {"schema_version": 1, "tasks": []}
    for split, prefix, case_start in (("development", "D", 0), ("reserved", "R", 5)):
        for number, (family, complexity, kind, issue, cases) in enumerate(SPECS, 1):
            ident = f"{prefix}{number:02d}"
            subset = [{"kind": kind, **data} for data in cases[case_start:case_start + 5]]
            public, hidden = subset[:2], subset[2:]
            base = f"{split}/{ident}"
            output[f"{base}/actor/app.py"] = (
                "import json, sys\n\n"
                "def solve(data):\n    raise NotImplementedError('implement the issue')\n\n"
                "if __name__ == '__main__':\n"
                "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n")
            checks = [f"assert solve({data!r}) == {reference_solve(data)!r}"
                      for data in public]
            output[f"{base}/actor/public_check.py"] = (
                "from app import solve\n" + "\n".join(checks) + "\n")
            output[f"{base}/issue.md"] = (
                "Implement `solve(data)` in `app.py` for the following service behaviour. "
                + issue + " Preserve the JSON-line command-line interface. "
                "Edit only `app.py`; the public check is a small example, not a full specification.\n")
            output[f"{base}/acceptance.json"] = json.dumps({
                "version": 1, "kind": "command", "criteria": ["public examples pass"],
                "constraints": ["Do not alter the issue, test or acceptance contract"],
                "required_outputs": ["app.py"],
                "protected_paths": ["public_check.py", "ISSUE.md", "acceptance.json"],
                "command": ["python3", "public_check.py"], "timeout_s": 10},
                indent=2) + "\n"
            output[f"oracles/{ident}.json"] = json.dumps({
                "schema_version": 1,
                "cases": [{"input": data, "expected": reference_solve(data),
                           "weight": 1, "milestone": f"case-{index}",
                           "critical": index == 1}
                          for index, data in enumerate(hidden, 1)]},
                indent=2, sort_keys=True) + "\n"
            assessment = {
                "task_kind": "investigation" if family == "diagnosis" else "implementation",
                "complexity": complexity, "verification": "executable",
                "context_tokens": 1200 if complexity == "routine" else 4000 if complexity == "moderate" else 9000,
                "deadline_seconds": None, "failure_cause": "none", "prior_local_repairs": 0,
                "frame_confidence": "clear", "required_artefacts": ["app.py"],
                "evidence": [{"source": "operator", "reference": "issue.md",
                              "claim": "service behaviour and bounded app.py edit"}]}
            catalogue["tasks"].append({
                "id": ident, "family": family, "split": split, "actor": f"{base}/actor",
                "issue": f"{base}/issue.md", "acceptance": f"{base}/acceptance.json",
                "oracle": f"oracles/{ident}.json", "allowed_edits": ["app.py"],
                "assessment": assessment})
    output["catalogue.json"] = json.dumps(catalogue, indent=2, sort_keys=True) + "\n"
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    planned = planned_files()
    drift = []
    for name, content in planned.items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                drift.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if drift:
        raise SystemExit(f"N5 corpus drift: {', '.join(drift)}")
    print(json.dumps({"files": len(planned), "tasks": 24,
                      "sha256": hashlib.sha256(json.dumps(planned, sort_keys=True).encode()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
