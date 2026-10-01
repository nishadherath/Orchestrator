"""In-memory tenant feature service."""

def run(request):
    store={tenant:dict(values) for tenant,values in request["store"].items()}
    cache={}
    results=[]
    for op in request["operations"]:
        tenant,feature=op["tenant"],op["feature"]
        if op["op"]=="update":
            store[tenant][feature]=op["value"]
            results.append({"status":"updated"})
            continue
        key=feature
        if key in cache:
            value,source=cache[key],"cache"
        else:
            value,source=store[tenant][feature],"store"
            cache[key]=value
        results.append({"value":value,"source":source})
    return {"results":results}
