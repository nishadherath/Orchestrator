#!/usr/bin/env python3
"""Generate chunk-01.txt through chunk-06.txt: plain-noun filler, deterministic
(seed 14), 350 numbered lines of ten words each per file (docs/PLAN-4.md
Stage B.1, docs/COMPACTION-DESIGN.md section 13.7). Six files, not five:
this shape's constraint is not reading chunk-03.txt, so it needs one more
file than T12/T13 to keep five files actually read. See
test/fixtures/benchmark/T12/repo/make_chunks.py for why plain nouns (D72).

Committed alongside the files it produced; the harness does not run this
script, it only reads the committed .txt files.
"""
import random

WORDS = ("table chair window garden river mountain bicycle harbor market forest "
         "bridge castle meadow orchard tunnel lantern compass anchor blanket kettle").split()

def main() -> None:
    rng = random.Random(14)
    for i in range(1, 7):
        lines = [f"file{i:02d} line{n:05d}: " + " ".join(rng.choice(WORDS) for _ in range(10))
                 for n in range(1, 351)]
        with open(f"chunk-{i:02d}.txt", "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
