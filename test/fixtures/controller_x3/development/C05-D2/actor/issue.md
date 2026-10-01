# Page selection reads the whole index

The report index is sorted by record ID. The page endpoint returns the right
IDs, but its current implementation fetches the entire index before slicing.
For each request, fetch only the requested page while preserving offset, limit
and order. The fixed adapter reports how many rows it fetched. The visible
smoke check covers only a tiny index. Record the observed read bound and a
next validation step in `report.json`.
