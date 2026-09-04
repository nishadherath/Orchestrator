<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (powershell)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# PowerShell: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Windows automation, deployment and operations tooling. PowerShell 7 (Core) unless the target mandates Windows PowerShell 5.1, and the mandate is written down.

**Checklist.**
- `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` at the top of every script.
- `[CmdletBinding()]`, typed and validated parameters.
- Functions emit objects, never formatted strings.
- `SupportsShouldProcess` on every state-changing function, so `-WhatIf` works.
- Run PSScriptAnalyzer and Pester in CI.

**Hazard.** Non-terminating errors that continue silently unless `$ErrorActionPreference` is set. `$null` on the right of a comparison, which does not do what the reader expects with arrays. Execution policy differences between machines.
