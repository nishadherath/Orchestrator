# Move the shared label formatter to its package

The formatter now belongs at `labels.format.render_label`. Move the existing
behaviour there, update both the API and batch consumers to import that path,
and remove `legacy_labels.render_label`. Preserve negative amounts and Unicode
customer names. Leave the JSON adapter and public check unchanged. Submit a
truthful `report.json` with observations and a next check.
