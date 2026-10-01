# Include the exact UI warning threshold

The UI should warn when an integer signal reaches or exceeds its configured
threshold. A value below the threshold should stay quiet. The local comparator
currently misses equality. Correct that boundary without changing nearby
values. A warning one point early is noisy but does not suppress a required
warning. Leave the JSON adapter and public smoke unchanged. Report the observed
behaviour and next check in report.json.
