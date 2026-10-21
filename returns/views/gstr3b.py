from django.contrib import messages
from django.shortcuts import render

from core.permissions import area_required
from returns.compute import build_gstr3b, purchase_lines, sales_lines
from returns.periods import parse_opening, parse_period, period_options


@area_required("returns")
def gstr3b(request):
    p = parse_period(request.GET)
    opening, problem = parse_opening(request.GET)
    for text in (p.problem, problem):
        if text:
            messages.warning(request, text)
    cid = request.me.company_id
    report = build_gstr3b(sales_lines(cid, p.start, p.end), purchase_lines(cid, p.start, p.end), opening)
    return render(request, "returns/gstr3b.html", {"p": p, "periods": period_options(p), "r": report, "opening": opening})
