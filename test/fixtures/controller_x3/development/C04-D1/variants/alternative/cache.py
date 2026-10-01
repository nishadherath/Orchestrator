"""Keep a separate feature map for each tenant."""


def process(request):
    tenants = {}
    answer = []
    for event in request["events"]:
        features = tenants.setdefault(event["tenant"], {})
        feature = event["feature"]
        if event["op"] == "put":
            features[feature] = event["value"]
            answer.append({"status": "stored"})
        else:
            answer.append({"status": "hit", "value": features[feature]}
                          if feature in features else {"status": "miss"})
    return {"results": answer}
