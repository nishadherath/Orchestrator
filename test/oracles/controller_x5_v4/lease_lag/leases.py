"""Reference lease semantics for protected audit."""

def run(request):
    lease=dict(request["lease"])
    results=[]
    for op in request["operations"]:
        if op["op"]=="renew":
            if op["owner"]!=lease["owner"] or op.get("token",lease["token"])!=lease["token"]:
                status="stale_owner"
            elif op["server_now"]>=lease["until"]:
                status="expired"
            else:
                lease["until"]=op["server_now"]+op["ttl"]
                status="renewed"
        elif op["op"]=="assign":
            lease["owner"]=op["owner"]
            lease["until"]=op["server_now"]+op["ttl"]
            lease["token"]+=1
            status="assigned"
        elif op["op"]=="ack":
            status=("acknowledged" if op["owner"]==lease["owner"] and
                    op["token"]==lease["token"] else "stale_owner")
        else:
            raise ValueError("unknown operation")
        results.append({"status":status,"token":lease["token"]})
    return {"results":results,"lease":lease}
