<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (html-css)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# HTML and CSS: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Every page a person reads. HTML is the content and structure; CSS is the presentation; JavaScript is an enhancement.

**Checklist.**
- Semantic elements; every form control labelled; every image has alt text or is marked decorative.
- Insert dynamic content with `textContent` or an escaping template, never `innerHTML` concatenation.
- Set a Content Security Policy; no inline scripts outside the build bundle.
- Run a validator and a WCAG 2.2 AA checker in CI.
- Honour `prefers-reduced-motion` and `prefers-color-scheme`.

**Hazard.** DOM-based cross-site scripting from one unescaped interpolation, and layout that assumes a viewport width.
