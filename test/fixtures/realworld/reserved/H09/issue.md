# Settle a shared result contract before updating consumers

Replace the tuple result with an immutable `Result(value, warnings)` contract,
then update both consumers to use named fields. Change only `shared/schema.py`,
`consumers/api.py`, and `consumers/export.py`.
