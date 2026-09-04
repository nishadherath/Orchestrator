<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (bash)
     Class:  Fable
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Bash: Fable-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.fable.md`.

---

**For.** Glue, build steps, CI, small operational tasks on Unix-like systems. Anything past a hundred lines or with non-trivial logic is rewritten in Python or Go.

**Illegal states.** `#!/usr/bin/env bash`, `set -euo pipefail`, and `IFS=$'\n\t'` at the top. Every expansion quoted. `[[ ]]` rather than `[ ]`. Arrays for lists. Every variable inside a function declared `local`.

**Errors.** `trap` for cleanup on `EXIT` and on signals. `mktemp` for every temporary path. An explicit exit code and a message to stderr on every failure path.

**Tooling.** `shellcheck` and `shfmt` in CI. `bats` for tests. `printf` rather than `echo` for anything that is data. No parsing of `ls` output. POSIX `sh` only when Bash is unavailable, and the script says so in its header.

**Hazard.** `set -e` does not fire inside a command substitution, a pipeline without `pipefail`, or a command used as a condition. Word splitting on an unquoted expansion. A `cd` that failed while the script kept going.

**Judgment.** `set -e` does not fire inside a command substitution, a pipeline without `pipefail`, or when the command is used as a condition; audit those three cases by hand, because the safety net you think you have does not cover them.
