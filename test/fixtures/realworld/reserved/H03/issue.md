# Import CSV batches atomically

Validate every `id,name` row before updating the supplied store. Reject malformed
or conflicting duplicate rows without partial writes, preserve existing data,
and make replay of an accepted batch idempotent. Change only `imports/csv_batch.py`.
