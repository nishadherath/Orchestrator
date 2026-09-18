# Select report records across an explicit timezone boundary

Given aware start and end instants and UTC record timestamps, select the
half-open interval `[start, end)`. Preserve stable ordering and repeatability.
Change only `reporting/window.py`.
