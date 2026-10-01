"""Convert integer minor units using an explicit rational quote."""


def convert(amount_minor: int, quote_numerator: int,
            quote_denominator: int) -> int:
    if quote_denominator <= 0:
        raise ValueError("quote denominator must be positive")
    return (amount_minor * quote_numerator + quote_denominator // 2) // quote_denominator
