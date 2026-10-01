"""Count record types in only the synthetic role transcripts; print no text."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("pass the exact synthetic project transcript directory")
folder = Path(sys.argv[1])
for transcript in sorted(folder.glob("*.jsonl")):
    messages = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = row.get("message")
        if row.get("type") != "assistant" or not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        text = "\n".join(item.get("text", "") for item in content
                         if isinstance(item, dict) and item.get("type") == "text")
        messages.append({"chars": len(text),
                         "tool_calls": sum(isinstance(item, dict) and
                                           item.get("type") == "tool_use"
                                           for item in content),
                         "premise": text.count('"type":"PremiseRecord"') +
                         text.count('"type": "PremiseRecord"'),
                         "frame": text.count('"type":"FrameRecord"') +
                         text.count('"type": "FrameRecord"'),
                         "candidate": text.count('"type":"CandidateRecord"') +
                         text.count('"type": "CandidateRecord"')})
    print(json.dumps({"transcript": transcript.name,
                      "assistant_messages": messages}, sort_keys=True))
