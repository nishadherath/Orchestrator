"""Freeze natural opening issue bodies from a predeclared event cohort."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
FRAME = ROOT / "test/results/2026-09-30-controller-x5-opening-frame-e.json"
BODIES = ROOT / "test/results/2026-09-30-controller-x5-opening-frame-e-selected-bodies.json"
PROTOCOL = "docs/stage-results/controller-x5-opening-event-frame-e-protocol-2026-09-30.md"
REPOS = (
    "pallets/werkzeug", "pallets/jinja", "pallets/flask",
    "pallets/itsdangerous", "pytest-dev/pluggy", "python-attrs/attrs",
    "python-trio/trio", "encode/httpx", "encode/httpcore",
    "agronholm/apscheduler", "aio-libs/yarl", "pydantic/pydantic-settings",
    "Textualize/rich", "pypa/packaging", "python-poetry/cleo",
    "psf/requests",
)
CUTOFF = "2026-09-26T00:00:00Z"
SEED = "x5-frame-e-2026-09-30-033927Z\n"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch(repo: str, page: int) -> tuple[list[dict], dict]:
    url = (f"https://api.github.com/repos/{quote(repo, safe='/')}/events"
           f"?per_page=100&page={page}")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Orchestrator-X5-provider-free-opening-frame",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=60) as response:
        raw = response.read()
        metadata = {"repository": repo, "page": page, "requested_url": url,
                    "final_url": response.geturl(), "status": response.status,
                    "server_date": response.headers.get("Date")}
    events = json.loads(raw)
    if not isinstance(events, list):
        raise ValueError(f"event API did not return a list: {url}")
    metadata["items"] = len(events)
    return events, metadata


def write_once(path: Path, value: object) -> str:
    if path.exists():
        raise FileExistsError(path)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if FRAME.exists() or BODIES.exists():
        raise FileExistsError("frame already frozen; no refresh or overwrite")
    rows: list[dict] = []
    bodies: dict[str, tuple[str, str | None]] = {}
    pages: list[dict] = []
    counts: list[dict] = []
    event_ids: set[str] = set()
    issue_urls: set[str] = set()
    for repo in REPOS:
        event_count = 0
        issue_count = 0
        for page in (1,):
            events, metadata = fetch(repo, page)
            metadata["earliest_event_at"] = min(
                (event["created_at"] for event in events), default=None)
            metadata["latest_event_at"] = max(
                (event["created_at"] for event in events), default=None)
            pages.append(metadata)
            event_count += len(events)
            for event in events:
                event_id = event["id"]
                when = event["created_at"]
                if not isinstance(event_id, str) or event_id in event_ids:
                    raise ValueError(f"duplicate or invalid event id: {repo} {event_id}")
                event_ids.add(event_id)
                if (when < CUTOFF or event["type"] != "IssuesEvent"
                        or event["payload"].get("action") != "opened"):
                    continue
                issue = event["payload"]["issue"]
                if "pull_request" in issue:
                    continue
                url = issue["html_url"]
                if url in issue_urls:
                    raise ValueError(f"duplicate opening issue: {url}")
                if issue["created_at"] > when:
                    raise ValueError(f"issue created after opening event: {url}")
                body = issue.get("body")
                title = issue["title"]
                if (body is not None and not isinstance(body, str)) or not isinstance(title, str):
                    raise ValueError(f"invalid opening text: {url}")
                issue_urls.add(url)
                rows.append({
                    "repository": repo, "event_id": event_id,
                    "event_created_at": when, "issue_created_at": issue["created_at"],
                    "url": url, "number": issue["number"], "title_sha256": digest(title),
                    "body_was_null": body is None, "body_sha256": digest(body or ""),
                })
                bodies[url] = (title, body)
                issue_count += 1
        counts.append({"repository": repo, "events_fetched": event_count,
                       "opening_issues_since_cutoff": issue_count})
    ordered = sorted(rows, key=lambda row: digest(SEED + row["url"]))
    selected = ordered[:30]
    selected_bodies = [{
        "position": position, "url": row["url"],
        "title": bodies[row["url"]][0], "title_sha256": row["title_sha256"],
        "body": bodies[row["url"]][1], "body_sha256": row["body_sha256"],
        "body_was_null": row["body_was_null"],
    } for position, row in enumerate(selected, 1)]
    frame = {
        "schema": "controller-x5-opening-event-frame-e-v1",
        "protocol": PROTOCOL,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repositories": REPOS, "event_cutoff_utc": CUTOFF,
        "hash_seed": SEED, "opening_issue_count": len(rows),
        "selected_count": len(selected),
        "selected_urls": [row["url"] for row in selected],
        "repository_counts": counts, "pages": pages, "rows": rows,
    }
    bodies_hash = write_once(BODIES, selected_bodies)
    frame_hash = write_once(FRAME, frame)
    print(json.dumps({"frame_sha256": frame_hash, "bodies_sha256": bodies_hash,
                      "opening_issues": len(rows), "selected": len(selected),
                      "pages": len(pages)}, sort_keys=True))


if __name__ == "__main__":
    main()
