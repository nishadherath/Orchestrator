import json
import sys

from journal import Journal


def execute(operations):
    journal = Journal()
    results = [journal.ingest(operation) for operation in operations]
    offsets = {f"{tenant}:{partition}": value
               for (tenant, partition), value in sorted(journal.offsets.items())}
    return {"results": results, "totals": journal.deliveries.totals,
            "offsets": offsets}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    json.dump(execute(request["operations"]), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
