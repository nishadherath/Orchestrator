# Sydney reporting windows misclassify boundary events

The daily report groups UTC event timestamps into the local calendar day for
Australia/Sydney. Events near midnight appear in the wrong day in winter and
summer. Keep ordinary same-day events correct, including the daylight-saving
offset. The adapter and public check are fixed. Record the cause, reproduced
boundary observations and the next check in `report.json`.
