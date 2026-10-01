"""Allocate integer cents in stable largest-remainder order."""


def allocate(total_cents: int, weights: list[int]) -> list[int]:
    if (not isinstance(total_cents, int) or isinstance(total_cents, bool)
            or total_cents < 0 or not weights
            or any(not isinstance(weight, int) or isinstance(weight, bool)
                   or weight < 0 for weight in weights)):
        raise ValueError("invalid allocation input")
    denominator = sum(weights)
    if denominator == 0:
        raise ValueError("weights must have a positive sum")
    products = [total_cents * weight for weight in weights]
    shares = [product // denominator for product in products]
    order = sorted(range(len(weights)),
                   key=lambda index: (-(products[index] % denominator), index))
    for index in order[:total_cents - sum(shares)]:
        shares[index] += 1
    return shares
