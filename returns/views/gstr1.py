from django.contrib import messages
from django.shortcuts import render

from core.permissions import area_required
from returns.compute import build_gstr1, invoice_documents, sales_lines
from returns.periods import parse_period, period_options


@area_required("returns")
def gstr1(request):
    p = parse_period(request.GET)
    if p.problem:
        messages.warning(request, p.problem)
    cid = request.me.company_id
    report = build_gstr1(sales_lines(cid, p.start, p.end))
    return render(request, "returns/gstr1.html", {
        "p": p, "periods": period_options(p), "r": report, "docs": invoice_documents(cid, p.start, p.end)})
