<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (html-css)
     Class:  Opus
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# HTML and CSS: Opus-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.opus.md`.

---

**For.** Every page a person reads. HTML is the content and structure; CSS is the presentation; JavaScript is an enhancement.

**Illegal states.** Semantic elements over generic ones. Every form control has a label. Every image has alternative text or is explicitly decorative. `lang` and viewport are set. Content is readable and navigable with JavaScript disabled.

**Errors.** Dynamic content is inserted with `textContent` or a templating layer that escapes; never by string concatenation into `innerHTML`. A Content Security Policy is set and inline scripts and styles are absent except for a single build-generated bundle.

**Tooling.** A validator and an accessibility checker (WCAG 2.2 AA) in CI. A performance budget for largest contentful paint and layout shift. `prefers-reduced-motion` and `prefers-color-scheme` honoured.

**Hazard.** DOM-based cross-site scripting from one unescaped interpolation, and layout that assumes a viewport width.

**Judgment.** A single unescaped interpolation into the DOM is a cross-site-scripting hole regardless of how trusted the data source looked at design time; treat every value that reaches the DOM as user input, including values that originated from your own database.
