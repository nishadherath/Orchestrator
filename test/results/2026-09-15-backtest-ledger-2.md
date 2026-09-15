# Ledger backtest, 2026-09-15 15:19 at 45614f2

Every recorded benchmark outcome (test/results/*benchmark*.md, excluding the B0-brief arm) fed into tools/route.py's posterior() in file order, against the shipped priors (docs/ROUTING-2-DESIGN.md section 5, docs/PLAN-2.md Stage 2.4, D64). No live claude -p call.

| Bucket | Floor posterior | Active rungs | Controller reason |
| :--- | :--- | :--- | :--- |
| mechanical/long/contained | 0.977 (12 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| mechanical/short/contained | 0.981 (17 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| open/long/contained | 0.994 (36 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| open/medium/contained | 0.833 (22 pass, 3 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| open/short/contained | 0.990 (26 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| structured/long/contained | 0.977 (12 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |
| structured/short/contained | 0.977 (12 pass, 0 fail) | ['worker-sonnet-low', 'worker-opus-high'] | none |

## Pass conditions (docs/ROUTING-2-DESIGN.md section 5)

- PASS: mechanical/long/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: mechanical/short/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: open/long/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: open/medium/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: open/short/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: structured/long/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: structured/short/contained: first stays the floor -- got 'worker-sonnet-low'
- PASS: open/medium/contained: worker-opus-high posterior mean >= 0.9 -- got 0.941 (2 pass, 0 fail)
- PASS: mechanical/long/contained: no intermediate sonnet rung activates -- none activated
- PASS: mechanical/short/contained: no intermediate sonnet rung activates -- none activated
- PASS: open/long/contained: no intermediate sonnet rung activates -- none activated
- PASS: open/medium/contained: no intermediate sonnet rung activates -- none activated
- PASS: open/short/contained: no intermediate sonnet rung activates -- none activated
- PASS: structured/long/contained: no intermediate sonnet rung activates -- none activated
- PASS: structured/short/contained: no intermediate sonnet rung activates -- none activated
- PASS: mechanical/long/contained: Controller decision is not proactive -- reason='none'
- PASS: mechanical/short/contained: Controller decision is not proactive -- reason='none'
- PASS: open/long/contained: Controller decision is not proactive -- reason='none'
- PASS: open/medium/contained: Controller decision is not proactive -- reason='none'
- PASS: open/short/contained: Controller decision is not proactive -- reason='none'
- PASS: structured/long/contained: Controller decision is not proactive -- reason='none'
- PASS: structured/short/contained: Controller decision is not proactive -- reason='none'
- PASS: mechanical/long/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: mechanical/short/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: open/long/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: open/medium/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: open/short/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: structured/long/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
- PASS: structured/short/contained: overflow posterior stays at its prior -- got 0.05, prior is 0.05 (n=0)
