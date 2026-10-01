# Shadow-column writes break rollback reads

A record has legacy and shadow value columns during a gradual cutover. While
both old and new readers remain deployed, writes in the shadow and cutover
phases must update both columns so a rollback reader sees the latest value.
The adapter and public smoke check are fixed; it observes only the selected
reader after a write. Record the missing write path, two reproduced reader
observations and the next rollback check in `report.json`.
