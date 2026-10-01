# Retried jobs lose request context

The queue adapter forwards a job on its first attempt, but retried jobs can
lose the tenant and trace context carried by the original job. Preserve both
fields through retries without changing the job payload or identifier. A job
must never run without its tenant context. The adapter and public smoke check
are fixed. Record your reproduced observations and next safety check in
`report.json`.
