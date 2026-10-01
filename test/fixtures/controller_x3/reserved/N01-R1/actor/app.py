#!/usr/bin/env python3
"""Stable JSON adapter exposes behaviour and active import provenance."""
import json
import sys

import api_client
import batch_job
import labels.format
import legacy_labels


def process(request):
    action = request["action"]
    if action == "direct":
        formatter = getattr(labels.format, "render_label", None)
        return ({"label": formatter(request["customer"], request["cents"])}
                if formatter else {"error": "missing-new-export"})
    if action in {"api", "batch"}:
        consumer = api_client if action == "api" else batch_job
        return {"label": consumer.make_label(request["customer"], request["cents"]),
                "source": consumer.render_label.__module__}
    if action == "exports":
        return {"new": hasattr(labels.format, "render_label"),
                "old": hasattr(legacy_labels, "render_label"),
                "api_new": api_client.render_label.__module__ == "labels.format",
                "batch_new": batch_job.render_label.__module__ == "labels.format"}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
