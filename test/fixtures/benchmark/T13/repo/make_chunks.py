#!/usr/bin/env python3
"""Generate chunk-01.txt through chunk-05.txt: plain-noun filler, deterministic
(seed 13), 350 numbered lines of ten words each per file, matching the shape
E30 calibrated (docs/PLAN-4.md Stage B.1, docs/COMPACTION-DESIGN.md section
13.7). See test/fixtures/benchmark/T12/repo/make_chunks.py for why plain
nouns, not Greek letters (D72).

Committed alongside the files it produced; the harness does not run this
script, it only reads the committed .txt files.
"""
import random

WORDS = ("table chair window garden river mountain bicycle harbor market forest "
         "bridge castle meadow orchard tunnel lantern compass anchor blanket kettle").split()

def main() -> None:
    rng = random.Random(13)
    for i in range(1, 6):
        lines = [f"file{i:02d} line{n:05d}: " + " ".join(rng.choice(WORDS) for _ in range(10))
                 for n in range(1, 351)]
        with open(f"chunk-{i:02d}.txt", "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
