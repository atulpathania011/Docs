from datetime import date

from django.shortcuts import render

from core.gst import fy_start_year
from core.permissions import area_required
from returns.compute import ZERO, purchase_lines, sales_lines
from returns.periods import parse_fy


@area_required("returns")
def returns_home(request):
    fy = parse_fy(request.GET)
    s_lines = sales_lines(request.me.company_id, date(fy, 4, 1), date(fy + 1, 3, 31))
    p_lines = purchase_lines(request.me.company_id, date(fy, 4, 1), date(fy + 1, 3, 31))
    rows = []
    for m in [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]:
        year = fy if m >= 4 else fy + 1
        s = [l for l in s_lines if (l["date"].year, l["date"].month) == (year, m)]
        p = [l for l in p_lines if (l["date"].year, l["date"].month) == (year, m)]
        out_tax = sum((l["tax"] for l in s), ZERO)
        itc = sum((l["tax"] for l in p if l["gstin"]), ZERO)
        rows.append({"value": f"{year}-{m:02d}", "label": date(year, m, 1).strftime("%B %Y"),
                     "invoices": len({l["doc_id"] for l in s}), "purchases": len({l["doc_id"] for l in p}),
                     "taxable": sum((l["taxable"] for l in s), ZERO), "out_tax": out_tax, "itc": itc, "net": out_tax - itc})
    this_fy = fy_start_year(date.today())
    fys = [(y, f"{y}-{str(y + 1)[-2:]}") for y in range(this_fy, this_fy - 4, -1)]
    if fy not in [y for y, _ in fys]:
        fys.append((fy, f"{fy}-{str(fy + 1)[-2:]}"))
    return render(request, "returns/home.html", {"rows": rows, "fy": fy, "fy_label": f"{fy}-{str(fy + 1)[-2:]}", "fys": fys})
