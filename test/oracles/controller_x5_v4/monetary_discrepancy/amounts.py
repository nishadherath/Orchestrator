"""Reference final-total rounding for protected audit."""
from decimal import Decimal,ROUND_HALF_EVEN
CENT=Decimal("0.01")

def reconcile(request):
    total=sum((Decimal(v) for v in request["lines"]),Decimal("0"))
    rounded=total.quantize(CENT,rounding=ROUND_HALF_EVEN)
    value=f"{rounded:.2f}"
    return {"ledger":value,"statement":value}
