# Retry storms starve foreground work in the pool

The two-slot worker pool admits requests in arrival order. A burst of retries
can occupy both slots before a foreground request starts. Reserve one slot for
the first waiting foreground request when one exists, then fill the other slot
in original arrival order so retries still progress. If no foreground work is
waiting, use all slots for retries. The adapter and public smoke check are
fixed. Report the observed cause and a safe follow-up check in `report.json`.
