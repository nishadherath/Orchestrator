# Fix configuration precedence

The Click consumer resolves one setting from four sources. An explicit CLI
value must win over the environment, which must win over the file, which must
win over the default. Values such as `0`, `false`, and the empty string are
explicit values rather than missing values. Change only `consumer/config.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
