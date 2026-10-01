"""Visible smoke check. The protected checker covers incident boundaries."""
from payments import process

request = {"attempts": [{"tenant": "west", "key": "fresh", "amount": 30,
                         "phase": "commit"}]}
assert process(request) == {"results": [{"status": "committed", "balance": 30}],
                            "balances": {"west": 30}}
