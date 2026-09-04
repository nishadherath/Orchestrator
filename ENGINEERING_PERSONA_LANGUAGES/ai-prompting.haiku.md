<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (ai-prompting)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# AI prompting: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Anything only a model can do: judgement over unstructured text, synthesis, generation, classification where no deterministic rule exists. Not for anything a parser, a regex or a lookup answers.

**Checklist.**
- Use a model only when a parser, regex or lookup cannot answer the question.
- Force output through a schema or tool call; never parse free text.
- Order the prompt: identity and standards, then tools, then reference material, then the task, then the most recent state.
- One job per prompt; split anything that does two things.
- Pin the model identifier in config, never in the prompt body.
- Run the regression suite (fixed inputs, evaluated outputs, cost, latency) before shipping any prompt change.

**Hazard.** Behaviour drifts silently on model updates. A prompt that passed last quarter is a hypothesis this quarter. Re-run the evaluation on any model or version change, and treat a version bump as a code change.
