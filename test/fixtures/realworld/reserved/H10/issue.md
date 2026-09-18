# Clarify retention before deleting exports

The request "clean up old exports" omits both the retention period and protected
categories. If no decision is supplied, raise `NeedClarification` without
changing data. Then delete only rows older than the chosen period whose category
is not protected. Change only `exports/retention.py`.
