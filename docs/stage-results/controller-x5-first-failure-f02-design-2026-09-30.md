# X5 F02: styled help width development case

Date: 2026-09-30 Australia/Sydney. Status: frozen provider-free fixture;
live producer pending. F02 is independent of F01 and is not an X6 reserve
case. It uses the BSD-3-Clause Click working tree at pinned local HEAD
`06b2a678741131fd577ce170e23e5ca0aeba0309`. The defects are authored
regressions on that source, **not** claims about upstream bugs.

The issue asks for ANSI-styled help text to wrap by visible terminal width
while preserving the escape sequences, ordinary text, paragraphs and
truncated output. Two source files are editable: `click/formatting.py` and
`click/_textwrap.py`. The frozen
[F02 catalogue](../../test/fixtures/controller_x5_first_failure/catalogue-f02-r2.json)
has SHA-256 `5a4e09fd030d899eed5750359af70a1b7527794117927f9a5fca038dab6b1389`
and binds the actor, three repair overlays and external protected oracle.
The earlier `catalogue-f02.json` is a superseded, provider-free calibration
draft in which the partial overlay fixed the less discriminating module.

| Variant | Public check | Protected checks |
| --- | --- | ---: |
| Authored baseline | fail, 2/3 public failures | 3/7 |
| One-module partial repair | fail | 6/7 |
| Original upstream files | pass | 7/7 |
| Separate explicit ANSI-stripping repair | pass | 7/7 |

The protected oracle exercises a styled word, styled first and later indents,
paragraphs, a styled usage prefix, and unstyled wrapping and usage. These are
behavioural calibration results, not a prediction of live worker failure or
Controller uplift. The [single-use F02 driver](../../tools/controller_x5_first_failure_f02.py)
uses the same settled first-failure checkpoint and matched one-call S/A
comparison as F01. It captures the exact failed public output for both arms
and refuses a paid mode without a dated exact-manifest notice. A first public
success ends the case. No case may be replayed to create a trigger.
