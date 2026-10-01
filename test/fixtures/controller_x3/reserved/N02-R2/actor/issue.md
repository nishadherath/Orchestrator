# Keep independent UI section renders independent

The section renderer makes headings and footers for independent UI items.
Each call must start with a fresh list of text parts. The heading and footer
helpers currently retain previous calls through mutable default arguments.
Fix both call paths. Preserve one-call output and leave the JSON adapter and
public smoke unchanged. Report observations and a next check in report.json.
