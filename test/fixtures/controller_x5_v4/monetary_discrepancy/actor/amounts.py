"""Cent-valued reports from decimal text inputs."""
from decimal import Decimal, ROUND_HALF_EVEN
CENT=Decimal("0.01")

def reconcile(request):
    lines=request["lines"]
    ledger=sum((Decimal(v).quantize(CENT,rounding=ROUND_HALF_EVEN) for v in lines),Decimal("0"))
    statement=Decimal(str(sum(float(v) for v in lines))).quantize(CENT,rounding=ROUND_HALF_EVEN)
    return {"ledger":str(ledger),"statement":str(statement)}
