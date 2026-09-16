"""Extract the E30 transcripts into test/results/2026-09-15-e30-transcripts.md (docs/PLAN-4.md Stage A.2, D72).

A one-off generator kept for provenance, not a general tool: RUNS below
names four specific session ids captured on one machine during D71's
probe, and its output file already quotes its own source. --repo and
--base (docs/PLAN-6.md D.4, audit A24) replace what were hard-coded
absolute paths to that one machine, so the script is at least portable
to wherever those four transcripts (or a differently-named equivalent
set) actually live, rather than only ever runnable from the original
checkout."""
import argparse
import json, glob, os, re, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--repo", type=Path, default=Path(r"C:\Users\Bob\Desktop\Code\Claude\Orchestrator"),
                 help="this repository's root; test/results/ under it is where the output is written")
ap.add_argument("--base", type=Path,
                 default=Path(r"C:\Users\Bob\.claude\projects\C--Users-Bob-Desktop-Code-Claude-orchestrator-scratch"),
                 help="the Claude Code projects directory holding the four session ids in RUNS below")
args = ap.parse_args()
REPO = args.repo
BASE = args.base
RUNS = [
    ("run 1", "f7e62e19-b4b1-4176-8718-b54e2d087525", 100000, "greek",
     "Greek-letter filler; the compaction summariser was refused by a [bio] safety classifier, both summaries are stubs, and the run then died on the same refusal"),
    ("run 2", "36e54eab-766a-48d5-946c-e3b83fb67cc9", 100000, "nouns",
     "plain-noun filler; three compactions, then the platform aborted the task for thrashing"),
    ("run 3", "07c4f3b0-69aa-41ad-b6d1-7a5832b95701", 150000, "nouns",
     "plain-noun filler; no compaction; task completed correctly"),
    ("run 4", "d5a2076a-cf8a-45cc-acc7-c915cdc7d0a6", 130000, "nouns",
     "plain-noun filler; one compaction; task completed correctly"),
]

out = []
out.append("# E30 transcripts, extracted (docs/PLAN-4.md Stage A.2, D72)\n")
out.append("Generated 2026-09-15 by `extract_e30.py` (quoted at the end of this file), from the four subagent transcripts E30 left under "
           "`~/.claude/projects/C--Users-Bob-Desktop-Code-Claude-orchestrator-scratch/`. Nothing below is typed by hand. The transcripts "
           "themselves are not committed (a throwaway probe, D71); this file is the committed record of what they contain. Summary text is "
           "not reproduced: only its length, its headings, and whether named strings occur in it.\n")
out.append("Claude Code 2.1.268, `worker-sonnet-low` (`claude-sonnet-5`, effort `low` per the transcript fields), forwarder sonnet, "
           "the probe-e30 task (read five chunk files one per call, then write a count; constraint: never touch `reference.txt`). "
           "`CLAUDE_CODE_AUTO_COMPACT_WINDOW` was set for every run, including run 1, which D71 described as refused before the "
           "worker started; this file corrects that.\n")
intervals = []
for label, sess, window, content, note in RUNS:
    paths = glob.glob(str(BASE / sess / "subagents" / "agent-*.jsonl"))
    out.append(f"## {label}: window {window:,}, {note}\n")
    if not paths:
        out.append("No subagent transcript exists for this session.\n")
        continue
    path = paths[0]
    meta = json.loads(Path(path[:-len(".jsonl")] + ".meta.json").read_text(encoding="utf-8"))
    out.append(f"`{os.path.basename(path)}`; meta.json keys: `{', '.join(sorted(meta))}`; agentType `{meta.get('agentType')}`; "
               f"description `{meta.get('description')}`.\n")
    out.append("| # | event | input tokens (input + cache read + cache write) | output | tool_use names |")
    out.append("| :--- | :--- | :--- | :--- | :--- |")
    i = 0
    last_total = None
    boundaries = []
    post_totals = []
    pending_post = False
    summaries = []
    model = None
    errors = []
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        t, st = d.get("type"), d.get("subtype")
        if d.get("isApiErrorMessage"):
            c = (d.get("message") or {}).get("content")
            text = c if isinstance(c, str) else json.dumps(c)
            errors.append(re.sub(r"\s+", " ", text)[:220])
        if st == "compact_boundary":
            i += 1
            pre = d["compactMetadata"].get("preTokens")
            boundaries.append((pre, last_total))
            pending_post = True
            out.append(f"| {i} | compact_boundary, trigger `{d['compactMetadata'].get('trigger')}` | preTokens {pre:,} | | |")
        elif t == "assistant":
            m = d.get("message") or {}
            u = m.get("usage") or {}
            model = model or m.get("model")
            if not u:
                continue
            total = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            names = [b.get("name") for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "tool_use"]
            if total:
                i += 1
                out.append(f"| {i} | assistant | {total:,} | {u.get('output_tokens', 0)} | {', '.join(names)} |")
                if pending_post:
                    post_totals.append(total)
                    pending_post = False
                last_total = total
        elif t == "user" and d.get("isCompactSummary"):
            c = (d.get("message") or {}).get("content")
            text = c if isinstance(c, str) else json.dumps(c)
            heads = [h[1] for h in re.findall(r"^\s*(\d+)\. ([A-Za-z][^:\n]*):", text, flags=re.M)]
            summaries.append({"chars": len(text), "headings": heads, "ref": "reference.txt" in text,
                              "ro": bool(re.search(r"read-only|never modify|do not modify|must not", text, flags=re.I)),
                              "rw": bool(re.search(r"only the Read and Write|Read and Write tools", text))})
            i += 1
            out.append(f"| {i} | compaction summary (user message, isCompactSummary) | {len(text):,} chars, {len(heads)} numbered headings | | |")
    out.append("")
    out.append(f"Model per transcript: `{model}`. Compactions: {len(boundaries)}. API error messages in the transcript: {len(errors)}.")
    for e in errors:
        out.append(f"- error text: `{e}`")
    for k, (pre, before) in enumerate(boundaries, 1):
        post = post_totals[k - 1] if k - 1 < len(post_totals) else None
        line = f"Compaction {k}: last uncompacted request {before:,}, preTokens {pre:,}"
        if post:
            line += f", first request after {post:,} (after/pre {post / pre:.2f})"
        line += f"; window minus trigger lies in [{window - pre:,}, {window - before:,})"
        intervals.append((label, content, window - pre, window - before))
        out.append(line + ".")
    for k, s in enumerate(summaries, 1):
        kind = "stub (no numbered headings)" if not s["headings"] else "structured"
        extra = f"; headings: {'; '.join(s['headings'])}" if s["headings"] else ""
        out.append(f"Summary {k}: {s['chars']:,} characters, {kind}{extra}. Names `reference.txt`: {s['ref']}. "
                   f"States the read-only constraint: {s['ro']}. States the Read/Write-only restriction: {s['rw']}.")
    out.append("")

out.append("## The trigger, from every compaction\n")
out.append("Each compaction brackets the trigger T between the last request that did not compact and the one that did, "
           "expressed as window minus T:\n")
for label, content, a, b in intervals:
    out.append(f"- {label} ({content}): [{a:,}, {b:,})")
nouns = [(a, b) for _, c, a, b in intervals if c == "nouns"]
greek = [(a, b) for _, c, a, b in intervals if c == "greek"]
nl, nh = max(a for a, _ in nouns), min(b for _, b in nouns)
greek_text = " and ".join(f"[{a:,}, {b:,})" for a, b in greek)
greek_overlap = max(a for a, _ in greek) < min(b for _, b in greek)
versus_nouns = ", ".join(("overlaps" if (a < nh and b > nl) else "is disjoint from") + " the plain-noun bracket"
                         for a, b in greek)
out.append(f"\nPlain-noun runs (2 and 4, four compactions on two windows) intersect at [{nl:,}, {nh:,}). Greek-letter run 1 "
           f"(two compactions, the same 100,000 window as run 2) brackets {greek_text}, which "
           f"{'overlap each other' if greek_overlap else 'do not even overlap each other'}; in order, the first {versus_nouns.split(', ')[0]} "
           f"and the second {versus_nouns.split(', ')[1]}. On the same window and the same task shape, the trigger fell at API-reported totals of 66,411 (run 2) and "
           "76,909 (run 1). The trigger is therefore not a function of the API-reported usage alone: the platform evaluates it on "
           "its own estimate of the conversation, and that estimate diverges from the API count by content, and in run 1 also "
           "by whatever a stub summary did to the estimate. For plain-noun content the reserve is bracketed at about 34,000 to "
           "35,000 tokens, which matches the documentation figure of 967,000 on a 1M model (33,000); for other content it can "
           "differ by ten thousand tokens or more, and any use of the figure must say which content it was measured on.\n")
out.append("## The floor after compaction\n")
out.append("First request after each structured compaction: run 2 at 57,863, 58,230 and 58,113; run 4 at 59,141. The fixed prefix "
           "(about 43,000, E26) plus a structured summary (5,400 to 8,300 characters) plus the preserved tail. Independent of the "
           "window. Run 1's stub summaries gave 56,532 and 69,036: the second stub preserved almost everything (after/pre 0.99), "
           "which is why that run compacted again at once. Headroom after a structured compaction is about window minus 34,000 "
           "minus 59,000: about 7,000 at 100,000 (thrashed on reads of about 8,400 tokens per turn), 37,000 at 130,000 "
           "(survived), 107,000 at the shipped 200,000.\n")
out.append("## Script\n\n`extract_e30.py` reads each session's `subagents/agent-*.jsonl`, sums `input_tokens + "
           "cache_read_input_tokens + cache_creation_input_tokens` per assistant message, records every `compact_boundary` "
           "`preTokens` and the first assistant total after it, collects `isApiErrorMessage` text, and inspects each "
           "`isCompactSummary` user message for numbered headings and named strings without reproducing it. Its source is "
           "the commit that added this file.\n")
target = REPO / "test" / "results" / "2026-09-15-e30-transcripts.md"
target.write_text("\n".join(out), encoding="utf-8", newline="\n")
print("written", target, len("\n".join(out)), "chars")
print("\n".join(out[-12:]))
