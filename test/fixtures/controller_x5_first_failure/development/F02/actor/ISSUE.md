# Styled help text uses visible terminal width

ANSI-coloured command names and indents now consume their raw escape-byte
length when deciding where to wrap usage and help text. A visibly short
prefix is pushed onto a separate line; styled indents and words also wrap
before the visible width is reached. Keep escape sequences in the output,
but calculate the width users see. Preserve normal unstyled wrapping,
paragraphs and truncated output.

The local check is `python3 -B public_check.py`. Repair only
`click/formatting.py` and `click/_textwrap.py`. Do not edit the issue, public
check, licence or other package modules. Evaluation includes styled text,
styled indentation, long words, usage prefixes and unstyled behaviour.
