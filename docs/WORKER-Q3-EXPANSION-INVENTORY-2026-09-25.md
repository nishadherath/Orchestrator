# Q3 expansion: pinned public source candidates

Date: 2026-09-25 UTC. Status: **historical source-selection record; the
eight-family public gate is complete**. The later
[Q3 result](stage-results/worker-q3-public-2026-09-25.md) contains the
frozen material, measured outcomes and remaining Q3 decision. Statements
below about prospective setup and dispatch describe the state at source
selection, not the current state. The two-task
[B0 canary](stage-results/worker-q3-canary-2026-09-25.md) reached hidden
acceptance on both P01 and P02. The original eight-family public gate still
needs six independent tasks. No issue, oracle or new paid episode is approved
by the mere presence of a source candidate.

These seven upstream repositories were shallow-cloned into the git-ignored
`pilot-runs/q3-sources/` **before any worker saw a task from them**. `git
rev-parse HEAD`, the bundled licence files and `pyproject.toml` were read
locally. The line counts are physical lines of unmodified package `.py` files,
including blank and comment lines. Package file counts and bytes exclude
tests, documentation and the cloned `.git` directory. Each package currently
fits Q0's 1,000-20,000 Python-line and Q1's 200-file/5 MB boundaries; a
packaged actor must be checked again after issue and tests are added.

| Candidate | Pinned upstream commit | Licence at commit | Package `.py` files / lines / bytes | Prospective mechanism |
| :--- | :--- | :--- | ---: | :--- |
| [Click](https://github.com/pallets/click/tree/06b2a678741131fd577ce170e23e5ca0aeba0309) | `06b2a678741131fd577ce170e23e5ca0aeba0309` | BSD-3-Clause | 17 / 12,821 / 447,724 | CLI parameter and context contract |
| [urllib3](https://github.com/urllib3/urllib3/tree/48113e7a5fa3b98a61467afa6bcbb0f9b7ca7207) | `48113e7a5fa3b98a61467afa6bcbb0f9b7ca7207` | MIT | 35 / 12,281 / 434,534 | HTTP retry and redirect protocol |
| [Tenacity](https://github.com/jd/tenacity/tree/3e58094d3bc414975aad9eadf343a32bdb3b89b3) | `3e58094d3bc414975aad9eadf343a32bdb3b89b3` | Apache-2.0 | 12 / 2,445 / 82,819 | Synchronous/asynchronous retry state |
| [attrs](https://github.com/python-attrs/attrs/tree/8f767776326faaed11e6c2974798787f6e19b343) | `8f767776326faaed11e6c2974798787f6e19b343` | MIT | 19 / 6,428 / 196,590 | Spare; no qualifying multi-module issue selected |
| [PyJWT](https://github.com/jpadilla/pyjwt/tree/1d41a6478e1562e68ff667fcd703356acf085f68) | `1d41a6478e1562e68ff667fcd703356acf085f68` | MIT | 12 / 3,247 / 115,256 | Key/claim validation with conflicting evidence |
| [packaging](https://github.com/pypa/packaging/tree/10590c194edb33c82f84a127883d6097c56b7840) | `10590c194edb33c82f84a127883d6097c56b7840` | Apache-2.0 OR BSD-2-Clause | 22 / 12,545 / 475,255 | Requirement/marker parsing contract |
| [platformdirs](https://github.com/tox-dev/platformdirs/tree/9ce60680d1fec795a02b1bff5afff1c1f203c10a) | `9ce60680d1fec795a02b1bff5afff1c1f203c10a` | MIT | 8 / 3,147 / 123,602 | Directory creation side effects |

The exact bundled licence SHA-256 values are Click `9a8ad106a394e853bfe21f42f4e72d592819a22805d991b5f3275029292b658d`,
urllib3 `130e3a64d5fdd5d096a752694634a7d9df284469de86e5732100268041e3d686`,
Tenacity `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd`,
attrs `882115c95dfc2af1eeb6714f8ec6d5cbcabf667caff8729f42420da63f714e9f`,
PyJWT `797a7a20231d4c433e9f1911db1731d06b5828b98f499819a034f7c0f56f5ce5`,
platformdirs `29e0fd62e929850e86eb28c3fdccf0cefdf4fa94879011cffb3d0d4bed6d4db6`,
and packaging's umbrella `LICENSE`
`cad1ef5bd340d73e074ba614d26f7deaca5c7940c3d8c34852e65c4909686c48`.
The packaging repository also contains `LICENSE.APACHE` and `LICENSE.BSD`.

The packages declare Python 3.10 or older as their minimum. On the planned
Linux Python 3.11+ host, their current `pyproject.toml` files declare no
mandatory runtime dependency: Click's `colorama` condition applies only on
Windows, and PyJWT's `typing_extensions` condition applies only below Python
3.11. Optional dependencies must not be
used by a task unless locked and included. None of the six has yet passed an
isolated actor import/setup test, and the possible mechanisms in the table
were hypotheses, **not completed task specifications**.

## Six prospective upstream regressions

Recent history was then inspected for actual fixes touching at least two
package modules and adding offline tests. These are issue candidates, not
validated tasks. The **starting tree is the exact parent of each fix**, so
the prospective actor sees a real pre-fix version rather than a synthetic
reversion. The fix commit and its tests are developer calibration material;
their content must not enter the actor. Issue descriptions must identify the
upstream report or fix accurately and remove clues to the reference patch.

| Family | Pre-fix starting commit | Upstream fix | Source modules changed by fix | Public mechanism |
| :--- | :--- | :--- | ---: | :--- |
| Click | `19fd4d6e18bc9fce451f92f422696b11169faa57` | [`831c8f0948af`](https://github.com/pallets/click/commit/831c8f0948af519e45b90801d7430ff25451f972) | 4 | Consistent command and option typo diagnostics |
| urllib3 | `f4e4bc31f40f8c94c6a1f1685df28f97ff48c305` | [`f5cf12234614`](https://github.com/urllib3/urllib3/commit/f5cf122346141b187cca0db6e6445297d336b610) | 3 | Explicit port zero through URL, pool and manager |
| Tenacity | `a09999688c8d3bb3d4ca1716748009954cc7c4d0` | [`389aab8b2688`](https://github.com/jd/tenacity/commit/389aab8b2688f7a1df41c2dd7797eeb18c8baff9) | 3 | Falsy retry waits in sync and async strategies |
| PyJWT | `ea7267519f2be5ff031efabd692af7a4461f3d5e` | [`384c945065ad`](https://github.com/jpadilla/pyjwt/commit/384c945065ad1f1d7e5a0331c7377c7f278532f5) | 3 | Parsed JWK-set cache and client consistency |
| packaging | `823b44ed1f904084a77ae3adf0ef130af6365f84` | [`48a8a0698052`](https://github.com/pypa/packaging/commit/48a8a069805291186522de3eff73ea80a8ca96ad) | 3 | Pickle-safe requirements and markers |
| platformdirs | `5118d32ca567aba27f0af81b7b5931e162e1b86b` | [`7d5c85d14e76`](https://github.com/tox-dev/platformdirs/commit/7d5c85d14e760688a2210c56148b4052e2355ba6) | 4 | Create only site directories returned to the caller |

The six parent worktrees were materialised separately under the ignored
`pilot-runs/q3-parents/`. Their package source and licences were remeasured
at the actual pre-fix commit, rather than assuming that newer-head measurements
apply:

| Parent family | Package files | Physical Python lines | Package bytes | Licence digest compared with newer head |
| :--- | ---: | ---: | ---: | :--- |
| Click | 18 | 11,473 | 396,957 | identical |
| urllib3 | 37 | 11,932 | 422,093 | identical |
| Tenacity | 13 | 2,409 | 80,974 | identical |
| PyJWT | 13 | 3,197 | 113,027 | identical |
| packaging | 21 | 9,544 | 358,350 | all three identical |
| platformdirs | 9 | 3,127 | 122,684 | identical |

The parent `pyproject.toml` files also declare a Python floor of 3.10 or
lower. Click needs `colorama` only on Windows; PyJWT needs
`typing_extensions` only below Python 3.11; the other four declare no
mandatory runtime dependency. An isolated WSL import and exact fixture
packaging check remain outstanding.

The issue frame was chosen before any new model response. attrs stays a spare
source because its inspected recent history did not yield a suitable
multi-module functional fix; it must not be silently substituted after
viewing a paid outcome.

The first Click ANSI candidate was rejected before any paid episode: one
nominally changed source file contained only a docstring edit, and the other
file alone reached hidden acceptance. Its prototype is retained under ignored
`pilot-runs/q3-rejected/P03-ansi/`, outside the public corpus. The replacement
Click task is an upstream **feature** at the pinned parent above. Its four
functional modules passed isolated calibration: baseline 10/100, a plausible
partial implementation 45/100, and both the upstream and a distinct correct
implementation 100/100. The content-addressed record is
`test/results/2026-09-25-worker-q3-p03-4177a184f67a-calibration.json`.

Before any new B0 dispatch, write one distinct issue per family, fix the
2-8 existing editable source paths, and independently grade baseline,
partial, clean reference, materially different correct variant and attack
variants with a root-owned oracle. Public checks must remain offline,
deterministic and nontrivial. Record the exact source-file inventory and
whether each fault is authored or an upstream issue. Exclude any family that
fails its licence, setup, size or grader gate, retaining the reason; freeze
replacement order before seeing paid outcomes. Only then freeze a six-task
manifest, dated spend notice and no-replay runner. These six public families,
along with P01/P02, cannot later enter Q4 reserved inference.
