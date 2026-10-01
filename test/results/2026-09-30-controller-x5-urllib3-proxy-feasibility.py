"""Provider-free local proxy redirect check for the pinned P04 urllib3 source."""

import http.server
import json
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test/fixtures/worker_q3_public/P04/actor"))

import urllib3  # noqa: E402


class Proxy(http.server.BaseHTTPRequestHandler):
    observations: list[dict[str, object]] = []

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        self.observations.append(
            {
                "host": parsed.hostname,
                "path": parsed.path,
                "authorization": "authorization" in self.headers,
                "cookie": "cookie" in self.headers,
                "proxy_authorization": "proxy-authorization" in self.headers,
                "ordinary": "x-correlation-id" in self.headers,
            }
        )
        if parsed.path == "/start":
            self.send_response(302)
            self.send_header("Location", "http://origin-b.invalid/final")
        else:
            self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    headers = {
        "Authorization": "Bearer dummy",
        "Cookie": "session=dummy",
        "Proxy-Authorization": "Basic dummy",
        "X-Correlation-ID": "public-control",
    }
    manager = urllib3.ProxyManager(f"http://127.0.0.1:{server.server_port}")
    outcomes: dict[str, object] = {}
    try:
        pool = manager.connection_from_url("http://origin-a.invalid/start")
        response = pool.urlopen(
            "GET",
            "http://origin-a.invalid/start",
            headers=headers,
            assert_same_host=False,
            timeout=urllib3.Timeout(total=2),
        )
        outcomes["low_level_status"] = response.status
        outcomes["low_level"] = list(Proxy.observations)
        Proxy.observations.clear()
        response = manager.request(
            "GET",
            "http://origin-a.invalid/start",
            headers=headers,
            timeout=urllib3.Timeout(total=2),
        )
        outcomes["high_level_status"] = response.status
        outcomes["high_level"] = list(Proxy.observations)
        outcomes["source_commit"] = "f4e4bc31f40f8c94c6a1f1685df28f97ff48c305"
        safe = all(
            len(observations) == 2
            and observations[0]["authorization"]
            and observations[0]["cookie"]
            and observations[0]["proxy_authorization"]
            and observations[1]["host"] == "origin-b.invalid"
            and not observations[1]["authorization"]
            and not observations[1]["cookie"]
            and not observations[1]["proxy_authorization"]
            and observations[1]["ordinary"]
            for observations in (outcomes["low_level"], outcomes["high_level"])
        )
        outcomes["observation_valid"] = safe
        outcomes["candidate_status"] = "no-vulnerable-baseline" if safe else "needs-review"
        output = Path(__file__).with_suffix(".json")
        output.write_text(json.dumps(outcomes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"observation_valid": safe, "candidate_status": outcomes["candidate_status"]}))
    finally:
        manager.clear()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
