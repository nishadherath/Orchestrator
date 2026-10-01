# X5 F03 first-failure development result

Date: 2026-09-30 Australia/Sydney. The F03
[manifest](../../test/results/2026-09-30-controller-x5-first-failure-f03-manifest.json)
and [dated notice](controller-x5-first-failure-f03-notice-2026-09-30.md)
bound one new producer and conditional matched S/A continuations. The final
offline harness passed **83/83**. WSL credential, Controller Graft and actor
preparation completed at zero provider spend before dispatch.

Observed: F03 adapted a [public Tenacity cancellation report](https://github.com/jd/tenacity/issues/529)
and added an authored async-default regression. Its baseline failed all three
public checks and passed 4/9 protected cases; an async-only partial repair
still failed public and passed 7/9. Two materially different complete repairs
passed public and 9/9. The live producer made exactly one Sonnet-low call.
Its served `claude-sonnet-5` receipt was terminal, writer-stopped and
identity-valid, settling **USD 0.2023272** reported API-equivalent with no
unresolved charge or breach. The public check passed on that first attempt;
protected grading scored **100/100** with zero critical errors. The
[result](../../test/results/2026-09-30-controller-x5-first-failure-f03-run/producer-result.json)
records `accepted`, `qualified: true`, `eligible: false` and 89.829 seconds
for the producer phase. No S or A successor started. Do not replay F03.

Inference: a more ambiguous issue with two possible repair layers also
failed to create a first public failure. Across R3, R4, P02, F01, F02 and
F03, six one-call producers reported **USD 0.799667001** API-equivalent and
yielded zero matched Controller comparisons. This set was selected for
development and is too small and heterogeneous to estimate a population
failure rate, but it is enough to stop paying for more cases of the same
shape without a new headroom premise.

Unknown: whether a different real task distribution would yield public
first-failure headroom and whether Controller would improve a matched repair.
The exact failed-report S/A path remains provider-free qualified, not live
validated. A post-success review selected by a public-only risk signal is a
distinct hypothesis requiring fresh cases, a fair direct-worker control and
separate cost accounting. F03's protected score cannot select such a route
retrospectively. B0 remains the shipping default; X6 remains sealed.
