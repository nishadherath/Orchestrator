# Customer import loses a row after restart

The new customer store is read by live billing exports. After an importer
restart, one source row was absent and a different customer's newer record
reverted to an older value. Exported bills cannot be recalled by changing a
status flag. Source omission, checkpoint timing and stale-version replay are
plausible causes. Use trace.json and distinguishing probes before changing
migration.py.

Source rows are in checkpoint order; checkpoint is the count of durably
processed rows. A first pass may fail after fail_after writes, then resume
from the durable checkpoint. A row may replace a target record only at a
higher version. Tombstones are versioned records and must not be resurrected
by an older value. Preserve records outside the source range and report the
checkpoint at crash and completion. Submit report.json with observed probes,
causal diagnosis, completion claim and the next verification step.
