import re


PRICE_PATTERN = re.compile(r"[£$€]([\d.]+)")


def extract_price(text: str) -> str | None:
    """Extract the numeric portion of a price string (e.g. '$22.12' → '22.12')."""
    match = PRICE_PATTERN.search(text)
    return match.group(1) if match else None
