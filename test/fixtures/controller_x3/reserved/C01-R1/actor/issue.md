# Replayed sequence numbers lose independent events

An event feed retries deliveries. A repeated sequence number within one feed
and epoch is the same delivery, but different feeds and a restarted epoch have
independent sequence spaces. Preserve every independent event once, in arrival
order. The adapter and public smoke check are fixed. Record the cause, what
you reproduced and the next replay check in `report.json`.
