# X5 F01: fresh first-failure development case

Date: 2026-09-30 Australia/Sydney. Status: frozen provider-free fixture;
live producer and matched comparison are pending. This is a development case,
not an X6 reserve unit.

F01 uses the MIT-licensed `attrs` source from the clean local upstream checkout
at commit `8f767776326faaed11e6c2974798787f6e19b343`. The two defects are
authored regressions on that pinned source; they are **not** claims about an
upstream issue. The actor has 23 package files plus an issue, public check,
licence and acceptance contract. Only `attr/_make.py` and
`attr/validators.py` may be edited. The first regression leaves a generated
constructor alias unset when a field transformer inspects metadata. The
second restores validator state to enabled after an inner disabled context,
losing the previous outer or pre-disabled state.

The frozen [catalogue](../../test/fixtures/controller_x5_first_failure/catalogue.json)
records every actor file, each candidate overlay, the protected oracle and
its SHA-256 (`885d7d6483762f5e22dc355298114a9d337f84e3e1d39744ff8b031b46ff4d95`).
Provider-free calibration on isolated copies produced:

| Variant | Public check | Protected checks |
| --- | --- | ---: |
| Authored baseline | fail, 3/3 public failures | 2/6 |
| One-module partial repair | fail | 4/6 |
| Original upstream files | pass | 6/6 |
| Distinct alternative repair | pass | 6/6 |

The protected checks cover inheritance, a generator transformer, nested
validator suppression, exception exit, explicit aliases and ordinary
validation. They are outside the actor package. The variant spread verifies
the case has more than one successful repair path and that a partial edit can
remain publicly incomplete. It does not predict the worker's first-attempt
failure rate or any Controller effect.

The single-use [live driver](../../tools/controller_x5_first_failure_f01.py)
binds F01 to the existing WSL Sonnet-low Q3 actor, the public first-failure
checkpoint, one repair call per successor and a bounded Controller A arm.
It refuses provider calls without a dated notice for its exact manifest.
Protected grading occurs only after the public entry decision. The public
Controller packet includes the issue, public check, validator source and the
exact failed public output captured at the qualified checkpoint. The same
bounded diagnostic is included in both successors' worker prompts. Its hash
must match the independently rerun public check, and both actor copies carry
identical report bytes.
`attr/_make.py` is over the packet's per-file size cap, so the Controller may
inspect it through the prebuilt actor Graft graph and cite a smaller public
source if it has a substantive finding. This packet limitation must be
considered when interpreting an A-arm result.

F01 alone cannot establish uplift. A qualifying first public failure would
permit a matched S/A development comparison. A first public success ends F01.
The broader prospective set and X6 sample design remain separate work.
