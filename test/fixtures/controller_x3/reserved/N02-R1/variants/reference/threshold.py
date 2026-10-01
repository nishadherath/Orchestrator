"""Warn at and above the configured threshold."""


def classify(value, boundary):
    return "warn" if value >= boundary else "quiet"
