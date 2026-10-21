import calendar
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from core.gst import fy_start_year, money

MAX_CREDIT = Decimal("100000000000")


@dataclass
class Period:
    value: str          # '2026-10'
    start: date
    end: date
    label: str          # 'October 2026'
    problem: str = ""


def _month_start(year, month):
    return date(year, month, 1)


def parse_period(params, today=None):
    """?period=YYYY-MM; with nothing (or nonsense) given, the previous month."""
    today = today or date.today()
    prev = _month_start(today.year - 1, 12) if today.month == 1 else _month_start(today.year, today.month - 1)
    raw, chosen, problem = (params.get("period") or "").strip(), None, ""
    m = re.fullmatch(r"(\d{4})-(\d{2})", raw)
    if m:
        try:
            chosen = _month_start(int(m.group(1)), int(m.group(2)))
            if not 2000 <= chosen.year <= 2100:
                chosen = None
        except ValueError:
            chosen = None
    if raw and chosen is None:
        problem = "That return period was not valid, so the previous month is shown."
    chosen = chosen or prev
    end = date(chosen.year, chosen.month, calendar.monthrange(chosen.year, chosen.month)[1])
    return Period(chosen.strftime("%Y-%m"), chosen, end, chosen.strftime("%B %Y"), problem)


def period_options(selected, today=None):
    """About two financial years of months for the drop-down (the selected month is always included)."""
    today = today or date.today()
    fy = fy_start_year(today)
    months = [(fy - 1 + (i + 3) // 12, (i + 3) % 12 + 1) for i in range(24)]   # Apr of last FY .. Mar of this FY
    values = [f"{y}-{m:02d}" for y, m in months]
    if selected.value not in values:
        months.append((selected.start.year, selected.start.month))
        months.sort()
    return [(f"{y}-{m:02d}", _month_start(y, m).strftime("%B %Y")) for y, m in months]


def parse_fy(params, today=None):
    """?fy=2026 means April 2026 to March 2027. Returns the starting year."""
    today = today or date.today()
    try:
        fy = int(params.get("fy", ""))
        return fy if 2000 <= fy <= 2100 else fy_start_year(today)
    except ValueError:
        return fy_start_year(today)


def parse_opening(params):
    """Credit brought forward from earlier months (optional): ob_igst, ob_cgst, ob_sgst."""
    out, problem = {}, ""
    for head in ("igst", "cgst", "sgst"):
        raw = (params.get(f"ob_{head}") or "").strip()
        try:
            v = Decimal(raw) if raw else Decimal("0")
            if not v.is_finite() or not (0 <= v <= MAX_CREDIT):
                raise InvalidOperation
        except InvalidOperation:
            v, problem = Decimal("0"), "A 'credit brought forward' amount was not valid, so it was treated as 0."
        out[head] = money(v)
    return out, problem
