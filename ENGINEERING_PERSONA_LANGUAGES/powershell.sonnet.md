<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (powershell)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# PowerShell: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Windows automation, deployment and operations tooling. PowerShell 7 (Core) unless the target mandates Windows PowerShell 5.1, and the mandate is written down.

**Illegal states.** `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` at the top of every script. Advanced functions with `[CmdletBinding()]`, typed parameters, `[ValidateSet()]` and `[ValidateNotNullOrEmpty()]`. Functions emit objects, never formatted strings.

**Errors.** Terminating errors with `throw` or `Write-Error -ErrorAction Stop`. `try` and `catch` with the exception type named. `SupportsShouldProcess` on any function that changes state, so `-WhatIf` works.

**Tooling.** PSScriptAnalyzer in CI. Pester tests. Approved verbs only. No aliases in scripts. No `Invoke-Expression`. Output file encoding stated explicitly (`-Encoding utf8`).

**Hazard.** Non-terminating errors that continue silently unless `$ErrorActionPreference` is set. `$null` on the right of a comparison, which does not do what the reader expects with arrays. Execution policy differences between machines.
