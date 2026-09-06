Rename the function `compute_hash`, defined in `utils.py`, to
`compute_digest`, and update every import and call site across all thirty
`module_*.py` files so the code keeps working exactly as before. Do not
change any other behaviour, and do not touch `test_modules.py`.

When you are done, run this yourself and confirm it passes before reporting
back:

    python3 -m unittest discover -s . -p "test_*.py"
