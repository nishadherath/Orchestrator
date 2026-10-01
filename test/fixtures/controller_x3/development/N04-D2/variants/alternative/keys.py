"""Equivalent staged rotation expressed with an immutable tuple."""
ACCEPTED = ("green", "blue")
SIGNER = next(identifier for identifier in ACCEPTED if identifier == "green")
