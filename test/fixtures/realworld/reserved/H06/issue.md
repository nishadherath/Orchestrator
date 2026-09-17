# Deduplicate durable webhook deliveries

Deliveries carry an event ID and sequence. Process them in sequence, persist
pending work before invoking the sink, and reuse the event ID as the sink's
idempotency key so replay after a crash is safe. Change only `webhooks/dispatcher.py`.
