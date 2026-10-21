import re
from decimal import Decimal, InvalidOperation

from core.constants import GST_RATES
from core.gst import MAX_VALUE, RATE_STEP, ROUND_HALF_UP


def _rate(text, label, errors):
    text = text.strip()
    if not text:
        return None
    try:
        value = Decimal(text)
        if not value.is_finite() or not (0 <= value <= MAX_VALUE):
            raise InvalidOperation
        return value.quantize(RATE_STEP, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        errors.append(f"{label} must be a number (or left blank).")
        return None


def parse_item_form(post):
    """Returns (values, errors). values holds what to show again if there are errors."""
    raw = {k: post.get(k, "").strip() for k in ("name", "hsn", "unit", "gst", "sale_rate", "purchase_rate")}
    raw["unit"] = raw["unit"].upper()
    errors = []
    if not raw["name"]:
        errors.append("Enter the item name.")
    elif len(raw["name"]) > 200:
        errors.append("The item name is too long (200 characters at most).")
    if raw["hsn"] and not re.fullmatch(r"\d{4,8}", raw["hsn"]):
        errors.append("HSN/SAC must be 4 to 8 digits.")
    if raw["unit"] and not re.fullmatch(r"[A-Z0-9]{1,10}", raw["unit"]):
        errors.append("Unit must be a short code such as NOS or KGS.")
    try:
        gst = Decimal(raw["gst"])
        if gst not in GST_RATES:
            raise InvalidOperation
    except InvalidOperation:
        gst = None
        errors.append("Choose a GST rate from the list.")
    sale_rate = _rate(raw["sale_rate"], "Sale rate", errors)
    purchase_rate = _rate(raw["purchase_rate"], "Purchase rate", errors)
    clean = {"name": raw["name"], "hsn": raw["hsn"], "unit": raw["unit"], "gst_rate": gst,
             "sale_rate": sale_rate, "purchase_rate": purchase_rate}
    return raw, clean, errors
