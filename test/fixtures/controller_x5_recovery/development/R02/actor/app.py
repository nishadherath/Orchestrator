import json
import sys

from cache import DecisionCache
from decision import decide
from policy import PolicyStore


def execute(operations):
    policies = PolicyStore()
    cache = DecisionCache()
    results = []
    for operation in operations:
        if operation["action"] == "evaluate":
            tenant = operation["tenant"]
            flag = operation["flag"]
            user = operation["user"]
            context = policies.context(tenant, flag, user)
            result = cache.get(tenant, flag, user, context["version"])
            if result is None:
                result = decide(context)
                cache.put(tenant, flag, user, context["version"], result)
            results.append(result)
        else:
            policies.apply(operation)
    return {"results": results}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    json.dump(execute(request["operations"]), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
