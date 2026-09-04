<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (ai-prompting)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# AI prompting: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Anything only a model can do: judgement over unstructured text, synthesis, generation, classification where no deterministic rule exists. Not for anything a parser, a regex or a lookup answers.

**Illegal states.** Schema-forced output (a tool call or a structured-output mode) rather than free text that is parsed afterwards. Enumerated answers where the answer space is finite. A single prompt has a single job; a prompt that does two things is two prompts.

**Structure.** Ordered by change frequency for cache stability: identity and standards, then tool definitions, then reference material, then the task, then the most recent state. Instructions are positive (what to do) rather than negative (what to avoid) where the two are equivalent. Examples only where an evaluation shows they help, because each example is a recurring token cost. Prompts for smaller classes are shorter, more concrete and more imperative; prompts for larger classes state the goal and the constraints and leave the method open.

**Errors.** A model's error is a wrong output, and it is caught by validation at the boundary, never by trusting the text. Every model output is untrusted input.

**Tooling.** Prompts live in files with a hash recorded in the run manifest. Every prompt has a regression suite of fixed inputs with evaluated outputs, cost and latency lines, run on every prompt change and every model version change. Model identifiers are pinned in config and never appear in the prompt body. Proprietary syntax stays inside the provider adapter.

**Hazard.** Behaviour drifts silently on model updates. A prompt that passed last quarter is a hypothesis this quarter. Re-run the evaluation on any model or version change, and treat a version bump as a code change.
