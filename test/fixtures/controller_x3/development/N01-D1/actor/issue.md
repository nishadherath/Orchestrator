# Rename the money formatter across its consumers

Rename `format_cents` to `money_text` in the formatter, invoice and receipt
modules. Preserve the displayed amounts, including negative values. Remove the
old exported name after updating both consumers. Leave the JSON adapter and
public check unchanged. Submit a truthful `report.json` with observations and
a next step.
