#!/usr/bin/env python3
"""Writes chunk-01.txt through chunk-12.txt: 350 numbered lines of ten
words each, drawn from a small set of everyday nouns, deterministic
from a fixed seed. Twelve files, more than the five or six used
elsewhere, so reading all of them takes several minutes rather than
under one.

Committed alongside the files it writes; nothing reads this script at
run time, only the committed files it already produced.
"""
import random

WORDS = ("table chair window garden river mountain bicycle harbor market forest "
         "bridge castle meadow orchard tunnel lantern compass anchor blanket kettle").split()

def main() -> None:
    rng = random.Random(15)
    for i in range(1, 13):
        lines = [f"file{i:02d} line{n:05d}: " + " ".join(rng.choice(WORDS) for _ in range(10))
                 for n in range(1, 351)]
        with open(f"chunk-{i:02d}.txt", "w", encoding="utf-8", newline="\n") as f:
            # No trailing newline: with one, a line-numbered read of the
            # file renders one extra, empty line past the true last line,
            # and a naive count of "lines shown" comes out one too high.
            f.write("\n".join(lines))

if __name__ == "__main__":
    main()
