# Q4S S4 coordinator preflight correction

On 2026-09-26 UTC, the first S4 child manifest
`1d342647bc6087502e8ea6e837235743ec193e1d14b838230e7aa343fe1c94c9`
was invoked with `--run` inside WSL. The coordinator's provider-free auth
probe expects to launch WSL from Windows, so that nested invocation failed.
The S4 campaign directory and provider-call intent did not exist; no S4 model
call or charge occurred. The unused manifest and exact approval were preserved
as `test/results/2026-09-26-worker-q4s-s4-preflight-blocked-*.json`.

The S4 driver now rejects a non-Windows coordinator before preflight. Its
provider-free regression test passed. The corrected child manifest is
`5d51db8eed091668d984351ceba87f3b7bc531803b0f82743e2623ddb9e1e144`.
It retains the same frozen S2 task order, 18 episodes, 54-call ceiling and
USD 72 local allocation. The WSL root entry point remains `--episode` only.

The corrected Windows coordinator next stopped in provider-free auth preflight,
again before creating a campaign directory or provider-call intent. A redacted
launcher diagnostic showed that the isolated Claude.ai access token was too
near expiry. `claude auth status --json` still reported `loggedIn=true`, so
that status alone is insufficient. The WSL user's and root master's access
expiry were both past, while their refresh expiry remained in the future.
The documented interactive Claude.ai sign-in and checked sync helper must
finish before this exact S4 manifest can be dispatched. No S4 model call or
charge has occurred at this checkpoint.
