"""Local test keys for the gateway's tenant identity services."""

RED_SHARED = b"red-shared-demo-signing-key-000001"
BLUE_SHARED = b"blue-shared-demo-signing-key-00001"
BLUE_OLD = b"blue-old-demo-signing-key-0000001"
BLUE_2026 = b"blue-2026-demo-signing-key-00001"

TENANT_KEYS = {
    "red": {"shared": RED_SHARED},
    "blue": {"blue-old": BLUE_OLD, "blue-2026": BLUE_2026,
             "shared": BLUE_SHARED},
}

# Legacy lookup retained from the gateway's single-issuer deployment.
KEYS_BY_KID = {"shared": RED_SHARED, "blue-old": BLUE_OLD}
