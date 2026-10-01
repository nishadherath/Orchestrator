# Webhook receipts can repeat or arrive out of order

Each webhook delivery has its own stable delivery ID, customer, sequence and
amount. Applying a delivery changes the customer's total once. Repeating an ID
must not apply its effect again, even if the transport reports a different
sequence. Distinct IDs remain distinct when their sequence values match or
arrive out of order.

The fixed adapter and public smoke check cover one delivery. Repair
`receipts.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
