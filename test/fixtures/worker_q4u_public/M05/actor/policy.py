"""Retention schedule selected from a complete tenant intake record."""


RETENTION_DAYS = {
    ("premium", "EU"): 90,
    ("premium", "US"): 365,
    ("standard", "EU"): 30,
    ("standard", "US"): 180,
}


def retention_days(tier: str, jurisdiction: str) -> int:
    return RETENTION_DAYS[(tier, jurisdiction)]
