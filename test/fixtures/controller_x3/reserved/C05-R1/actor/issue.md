# Producer bursts grow the pending batch queue

A producer submits batches faster than one consumer drains them. `capacity`
limits the number of pending batches, not merely the size of each batch.
Once the queue is full, reject a new batch with an explicit `backpressure`
status. Never drop an accepted batch, and preserve first-in, first-out order
when the consumer drains the queue. Honour the configured capacity.

The fixed adapter and visible smoke check cover only one small batch. Repair
`queue.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
