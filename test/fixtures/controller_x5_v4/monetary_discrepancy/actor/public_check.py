from amounts import reconcile
assert reconcile({"lines":["1.00","-0.25"]}) == {"ledger":"0.75","statement":"0.75"}
