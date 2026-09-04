<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (bash)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Bash: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Glue, build steps, CI, small operational tasks on Unix-like systems. Anything past a hundred lines or with non-trivial logic is rewritten in Python or Go.

**Checklist.**
- `set -euo pipefail` and a quoted `IFS` at the top of every script.
- Quote every expansion; use `[[ ]]`, arrays, and `local` inside functions.
- `trap` for cleanup on `EXIT` and signals; `mktemp` for temp paths.
- Run `shellcheck` and `shfmt` in CI.
- Rewrite in Python or Go past roughly a hundred lines.

**Hazard.** `set -e` does not fire inside a command substitution, a pipeline without `pipefail`, or a command used as a condition. Word splitting on an unquoted expansion. A `cd` that failed while the script kept going.
