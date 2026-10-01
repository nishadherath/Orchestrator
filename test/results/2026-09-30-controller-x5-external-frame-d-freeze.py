"""Freeze the predeclared recent public issue frame without reading bodies."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
FRAME = ROOT / "test/results/2026-09-30-controller-x5-external-frame-d.json"
BODIES = ROOT / "test/results/2026-09-30-controller-x5-external-frame-d-selected-bodies.json"
REPOS = (
    "pydantic/pydantic",
    "pytest-dev/pytest",
    "pytest-dev/pytest-asyncio",
    "sqlalchemy/sqlalchemy",
    "sqlalchemy/alembic",
    "aio-libs/aiohttp",
    "agronholm/anyio",
    "celery/celery",
    "fastapi/fastapi",
    "Kludex/starlette",
    "encode/httpx",
    "encode/httpcore",
    "encode/uvicorn",
    "psf/requests",
    "urllib3/urllib3",
    "pallets/werkzeug",
    "pallets/click",
    "python-trio/trio",
    "astral-sh/ruff",
    "python-poetry/poetry",
)
CUTOFF = "2026-09-27T00:00:00Z"
SEED = "x5-frame-d-2026-09-30-015455Z\n"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch(repo: str, page: int) -> tuple[list[dict], dict]:
    url = (
        f"https://api.github.com/repos/{quote(repo, safe='/')}/issues"
        f"?state=open&sort=created&direction=desc&per_page=100&page={page}"
    )
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Orchestrator-X5-provider-free-frame",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=60) as response:
        raw = response.read()
        record = {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "server_date": response.headers.get("Date"),
            "items": None,
        }
    items = json.loads(raw)
    if not isinstance(items, list):
        raise ValueError(f"issue API did not return a list: {url}")
    record["items"] = len(items)
    return items, record


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
    included: list[dict] = []
    bodies: dict[str, str | None] = {}
    pages: list[dict] = []
    repo_stats: list[dict] = []
    for repo in REPOS:
        seen_urls: set[str] = set()
        previous_created: str | None = None
        count = 0
        for page in range(1, 51):
            items, page_record = fetch(repo, page)
            pages.append(page_record)
            for item in items:
                created = item["created_at"]
                if previous_created is not None and created > previous_created:
                    raise ValueError(f"non-descending created order in {repo} page {page}")
                previous_created = created
                if created < CUTOFF or "pull_request" in item:
                    continue
                url = item["html_url"]
                if url in seen_urls:
                    raise ValueError(f"duplicate issue in {repo}: {url}")
                seen_urls.add(url)
                body = item.get("body")
                if body is not None and not isinstance(body, str):
                    raise ValueError(f"unexpected body type: {url}")
                labels = [label if isinstance(label, str) else label["name"]
                          for label in item["labels"]]
                row = {
                    "repository": repo,
                    "url": url,
                    "number": item["number"],
                    "title": item["title"],
                    "created_at": created,
                    "updated_at": item["updated_at"],
                    "labels": labels,
                    "comments": item["comments"],
                    "body_was_null": body is None,
                    "body_sha256": digest(body or ""),
                }
                included.append(row)
                bodies[url] = body
                count += 1
            if not items or items[-1]["created_at"] < CUTOFF or len(items) < 100:
                break
        else:
            raise ValueError(f"50-page safety cap reached before cutoff: {repo}")
        repo_stats.append({"repository": repo, "included": count})
    ordered = sorted(included, key=lambda row: digest(SEED + row["url"]))
    selected = ordered[:30]
    selected_urls = [row["url"] for row in selected]
    selected_bodies = [{
        "position": position,
        "url": row["url"],
        "body": bodies[row["url"]],
        "body_sha256": row["body_sha256"],
        "body_was_null": row["body_was_null"],
    } for position, row in enumerate(selected, 1)]
    frame = {
        "schema": "controller-x5-external-frame-d-v1",
        "protocol": "docs/stage-results/controller-x5-external-recent-frame-d-protocol-2026-09-30.md",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repositories": REPOS,
        "created_cutoff_utc": CUTOFF,
        "hash_seed": SEED,
        "all_open_issue_count": len(included),
        "selected_count": len(selected),
        "selected_urls": selected_urls,
        "repository_counts": repo_stats,
        "pages": pages,
        "rows": included,
    }
    bodies_hash = write_once(BODIES, selected_bodies)
    frame_hash = write_once(FRAME, frame)
    print(json.dumps({
        "frame_sha256": frame_hash,
        "bodies_sha256": bodies_hash,
        "all_open_issues": len(included),
        "selected": len(selected),
        "pages": len(pages),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
