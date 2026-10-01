"""Reference tenant feature semantics for protected audit."""

def run(request):
    store={t:dict(v) for t,v in request["store"].items()}
    cache={}
    results=[]
    for op in request["operations"]:
        tenant,feature=op["tenant"],op["feature"]
        key=(tenant,feature)
        if op["op"]=="update":
            store[tenant][feature]=op["value"]
            cache.pop(key,None)
            results.append({"status":"updated"})
        elif key in cache:
            results.append({"value":cache[key],"source":"cache"})
        else:
            value=store[tenant][feature]
            cache[key]=value
            results.append({"value":value,"source":"store"})
    return {"results":results}
