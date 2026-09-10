Three commitments before the numbered answers, because they determine most of what follows.

A role earns separation only when it needs a different context (isolation), a different objective (adversarial), or a different cost tier. Otherwise it is a section of one prompt. Most multi-agent designs over-split and pay twice: coordination tokens and conformity.

The core of the system is a ledger, not a set of agents. Agents are stateless functions over typed records. This is a blackboard architecture, and it has survived forty years because it solves the interference problem by construction.

The fleet earns its cost in exactly three places: independent parallel generation, adversarial critique in a separate context, and tool-backed verification. A single strong model running the eight-step sequence from the previous answer gets roughly 70% of the value. Build that first. It is the baseline the fleet must beat, and if it does not beat it by a margin that pays for itself, you have a prompt, not a system.

### 1. Roles, rated by importance

Importance means how much output quality falls if the role is removed or done badly.

| # | Role | Function | Premise operation | Importance /10 |
|---|---|---|---|---|
| 1 | **Framer** | Premise ledger (every premise classified: law, maths, policy, habit, unverified), goal ladder, metric interrogation, problem-type classification, dissolution check, acceptance criteria, deductive baseline B0 | Remove, replace goal | 10 |
| 2 | **Verifier** | Measures unverified premises with tools, runs falsification tests, builds smallest concrete instances. The only role that touches reality | Add true premises | 9 |
| 3 | **Critic** | Blind adversarial review: failure modes, derivability flag (could this have been deduced from the ledger?), falsified-premise claims | Search | 8 |
| 4 | **Generators** (N isolated instances, one technique family each) | Candidate solutions | Remove, re-represent, add, replace goal | 7 each, 9 as a set |
| 5 | **Selector** | Scores candidates against acceptance criteria and B0, picks the instantiation shortlist | Search | 5 |
| 6 | **Librarian** | Structural pattern library, technique performance stats, false-premise catalogue. Read at generate, write at close | Add, cross-run | 4 now, rises with every run |
| 7 | **Controller** | State machine, budget, routing, termination. Code, not a model, apart from two judgment calls | None | Structural |
| 8 | **Scribe** | Schema validation, ledger writes, phase digests | None | Code |

Generators look like the point but are the most replaceable component: any capable model with a technique brief generates. Framer and Verifier are where a bad job silently poisons everything downstream, and no quantity of generation recovers from a wrong ledger or a hallucinated measurement.

Roles deliberately not created: Instantiator (it is the Verifier), Judge (it is the Selector), Reframer (the Framer re-entered), Human liaison (the Controller's gate points), Baseline solver (Framer output B0).

### 2. Attack and non-interference

The attack is the eight-step sequence with each step owned by one role. Non-interference comes from four mechanisms, none of which rely on agents behaving well.

**Phase gating on frozen artefacts.** No generator runs until ledger version n is frozen. Every candidate cites its ledger version; candidates against a stale version are rejected by the Scribe.

**Context isolation.** Generators never see each other. The Critic sees candidates, not generator reasoning. The Verifier gets a measurement task, not the whole problem. Independence is what makes N generators worth more than one; the Diehl and Stroebe result on human groups transfers directly to model ensembles that read each other.

**Single writer per record type.** Framer writes premises, Verifier writes measurements, generators append candidates, Critic appends critiques, Controller alone changes status fields. Nobody edits another's record; they emit new records that reference old IDs. Append-only, versioned.

**Typed contracts.** Each role has an input slice and an output schema. Schema failures are rejected before any model sees them.

Agents never talk. They read and write records. That is the whole answer to "getting in each other's way".

### 3. Orchestrator, thin and deterministic

Orchestrator. Peer-to-peer among model agents fails on three counts: conformity (agents that read each other converge on the first plausible idea), no natural termination, and no budget owner. Interaction adds value at exactly one point, refinement of a shortlisted candidate under critique, and even there it should be bounded.

So: hub-and-spoke for generation, a bounded two-round mediated debate for the top k, and a deterministic state machine for control.

```
run(problem, mode):
  L ← FRAME(problem)                        # ledger v1: premises, goal ladder, acceptance, B0
  human_gate(L.acceptance, L.goal_ladder)   # deep mode only
  repeat:
    M ← VERIFY(L.unverified where cost ≤ mode.verify_ceiling)
    L ← FRAME.update(L, M)
    if L.dissolved: return REFRAME(L)       # the problem stopped existing; report why
  until L.stable or verify_budget spent     # stable: no premise changed class this pass

  best ← B0
  for tier in mode.tiers:                   # quick: [1]   deep: [1, 2, 3]
    C ← parallel_isolated(GENERATE[t](L) for t in tier)
    K ← CRITIQUE(C, blind)
    if K.falsifies_any_premise: L ← FRAME.update(L, K); restart tier
    S ← SELECT(C, K, criteria=L.acceptance, baseline=best)   # top k by gain ÷ falsification cost
    for c in S:
      c' ← DEBATE(c, K[c], rounds=mode.debate_rounds)
      r  ← VERIFY.instantiate(c')           # cheapest falsification test first
      if r.meets(L.acceptance): return c' + audit trail
      L  ← L + premise("c' fails because r.reason", class=verified)
      best ← argmax(best, c')
  return best + gap_report(unmet criteria, unverified load-bearing premises, next cheapest test)
```

Termination: acceptance met, problem dissolved, budget spent, or two consecutive tiers without improvement over `best`. Convergence comes from the ledger monotonically gaining verified premises: every loop strictly shrinks the untested candidate space. That is the property peer-to-peer systems lack.

The Controller makes two model calls per run: "is the ledger stable enough to freeze" and "which technique families for this problem type". Both are classification, both go to the cheapest cell, and the second is replaced by Librarian statistics once there are enough runs.

### 4. Workflow and iterative validation

| Phase | Owner | Artefact produced |
|---|---|---|
| Intake | Controller | ProblemRecord: statement, context, constraints, budget, mode, acceptance criteria if supplied |
| Frame | Framer | Ledger v1: premises (id, text, class, source, confidence, cheapest verification method), three-rung goal ladder, metric analysis, problem type, dissolution verdict, acceptance criteria (proposed if absent), B0 |
| Verify | Verifier | MeasurementRecords: premise id, method, result, artefact link (log, output, dataset). No artefact, no record |
| Generate | Generators | CandidateRecords: technique, ledger version, premise operation, mechanism, claimed gain vs B0, premises introduced, cheapest falsification test, cost estimate |
| Critique | Critic | CritiqueRecords: ranked failure modes, derivability flag, falsified-premise claims, verdict |
| Select | Selector | Shortlist with scores |
| Instantiate | Verifier | Smallest concrete instance, falsification test run, EvaluationRecord |
| Close | Librarian | SolutionRecord or GapReport, library write-back |

Validation is iterative through the ledger, not through editing a candidate in place. A failed candidate becomes a verified negative premise; refinement is a candidate v2 that references the failure record. This gives convergence and an audit trail that states why every alternative was rejected.

Acceptance criteria are fixed before generation, always. Deciding what "done" means after seeing candidates is how exotic-but-worse solutions get accepted.

### 5. Models and effort per role

Five effort levels exist (low, medium, high, xhigh, max); Opus 5 supports all five, and max is available on Fable 5, Opus 5 and Sonnet 5 among others. Assignments below use your sonnet/opus/fable cell scheme.

| Role | Quick | Deep | Reason |
|---|---|---|---|
| Controller calls | sonnet/low | sonnet/low | Classification, not reasoning |
| Framer | opus/high | fable/xhigh | Highest value per token in the system; a wrong ledger wastes everything after it |
| Verifier | sonnet/medium | sonnet/high, opus/high for experiment design | Many cheap tool calls; correctness comes from artefacts, not reasoning |
| Generators, tier 1 (subtract, re-represent, abduce) | sonnet/high ×3 | opus/high ×5 | Structured techniques; mid-size models run them well from a good brief |
| Generators, tier 3 (analogy, lens rotation, side channel) | not run | fable/xhigh ×3 | Retrieval breadth is the bottleneck; the largest model has the widest pool |
| Critic | opus/medium | opus/high, second pass by a different class from the generator | Must be at least as strong as what it reviews or it rubber-stamps; a different class reduces correlated blind spots |
| Debate | not run | opus/high both sides | |
| Selector | sonnet/medium | opus/medium | Scoring against explicit criteria |
| Librarian write-back | sonnet/medium | sonnet/high | Abstraction to relational form is compression |

Two rules. Critic class is never below generator class. Generators cap at xhigh: max removes the token constraint and my prior is that the marginal tokens go to verbosity rather than retrieval breadth, but measure it on your evals before trusting the prior.

Cache layout: `[static system + technique library + schemas] | [ledger v_n] | [role brief]`. Generators share the first two blocks; a ledger bump invalidates only the second. Cache hits on the ledger are what make N parallel generators affordable.

### 6. Inter-agent communication

Blackboard, not chat. Records in, records out. Chat between agents leaks reasoning (kills independence), invites conformity, is unauditable, and spends tokens on restatement.

- Every message is a typed record with an ID and references. Free text only inside designated fields with length caps.
- Agents receive slices, not history: ledger, brief, and the records their contract names. Never a transcript.
- The Controller emits a phase digest under 300 tokens at each transition. That is the only summarisation in the system.
- Direct exchange exists only in DEBATE: two rounds, mediated, both sides writing records.
- Overflow policy: pass records whole; on genuine input-window overflow, trim largest-first, never the ledger or the acceptance criteria, and disclose the trim to the agent and the log. Your v14 truncation bug in the Wu Xing engine is the failure this prevents.

### 7. Memory

Three tiers with different lifetimes and write rights.

**Run-scoped shared (the blackboard).** Ledger, measurements, candidates, critiques, evaluations, decision log, budget ledger. Shared read, single writer per type, append-only, versioned, persisted so a run resumes from any phase.

**Role-private ephemeral.** Generator scratch, Verifier sandbox state, Critic checklist state. Discarded at phase end. Persisting these contaminates independence in later phases and in future runs.

**Cross-run persistent (the library).** Written only by the Librarian at close, with outcome labels:
- Structural pattern library: relational form → solutions that worked, domain tags, source runs. Indexed by form, never by domain.
- Technique performance: measured hit rate and cost per technique per problem type. This replaces my guessed rates with real ones and drives Controller routing after about fifty runs.
- False-premise catalogue: premises that turned out false, by domain. The Framer reads it first; the fastest way to find the false premise in a new problem is to know which ones are usually false.
- Failure records: candidate shapes that failed and why.

Not retained: reasoning traces, transcripts, generator scratch. Storage cost, contamination risk, no training signal.

### 8. Quick versus deep

Mode is a parameter vector, not a different system.

| Dial | Quick | Deep |
|---|---|---|
| Verify cost ceiling | One tool call, no code | Full experiments, prototypes |
| Goal ladder | One rung | Three rungs plus dissolution check |
| Tiers | 1 | 1, 2, 3 |
| Generators | 3 | 8 to 12 |
| Critique | One pass | Two passes, second by a different class, plus debate |
| Instantiation | None; paper falsification only | Top 3 |
| Human gates | None | Acceptance criteria; pre-instantiation |
| Stop rule | First candidate surviving critique with no unverified load-bearing premise, else B0 | Acceptance met or budget spent |
| Output | Best plus ranked alternatives plus explicit unverified-premise list | Solution plus audit trail |
| Model calls | 5 to 10 | 50 to 200 |

The non-negotiable in quick mode: the output names which premises are unverified and load-bearing. Quick mode's risk is not a worse answer; it is a confident answer resting on an unmeasured premise. A middle mode adds the verify loop and one critique round and covers most real work.

### Other questions that matter

**How do you stop novelty theatre?** Every candidate is scored against B0, and the Critic's derivability flag separates "new" from "exotic". An exotic candidate that loses to B0 is discarded however clever it reads.

**How do you stop hallucinated verification?** No measurement record without an artefact. The Verifier runs sandboxed. The Critic's second pass re-executes any measurement a shortlisted candidate depends on.

**Where is the human?** Three gates in deep mode: confirm acceptance criteria and goal ladder (cheap, high leverage), approve before expensive instantiation, accept final. Never inside generation.

**How does the system itself fail, and what caps it?** Ledger bloat (cap 40 premises; Framer must merge). Controller loops (hard cap of three reframes). Cost blow-up (per-phase budget caps; escalation requires headroom). Conformity leaking through the library (entries are relational forms, not verbatim solutions; a generator receives at most three retrieved patterns). Critic too strict, which is the failure your Censor had before v11: passing is the expected outcome, returns only for material defects, and the return rate is tracked and recalibrated if it exceeds roughly 40%.

**What is the training signal?** Which technique produced the winner, per problem type, per run. Log it from day one. Nothing else in the system improves without it.

**What is the actual IP?** The technique library: the forty techniques from the previous answer, each as a brief with trigger question, premise operation, output schema, and three worked examples written in relational-form language. The agents are commodity. The briefs and the accumulated library are not.
