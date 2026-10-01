"""Public formatter after package migration."""


def render_label(customer, cents):
    sign = "-" if cents < 0 else ""
    absolute = abs(cents)
    return f"{customer} | {sign}USD {absolute // 100}.{absolute % 100:02d}"
