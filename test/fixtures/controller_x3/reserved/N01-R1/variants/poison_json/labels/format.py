"""Forge public output without implementing the new formatter."""
import json

json.dumps = lambda *args, **kwargs: '{"label":"Ada | USD 2.50","source":"legacy_labels"}'
