from django.http import Http404

from core.constants import STATES
from core.permissions import area_required
from core.statement import csv_response
from returns.compute import build_gstr1, build_gstr3b, purchase_lines, sales_lines
from returns.periods import parse_opening, parse_period


def _pos(code):
    return f"{code}-{STATES.get(code, '')}"


@area_required("returns")
def export_csv(request, table):
    p = parse_period(request.GET)
    cid = request.me.company_id
    s_lines = sales_lines(cid, p.start, p.end)
    name = f"{table}-{p.value}.csv"
    if table == "b2b":
        rows = build_gstr1(s_lines)["b2b"]
        return csv_response(name, ["GSTIN of recipient", "Receiver name", "Invoice number", "Invoice date", "Invoice value",
                                   "Place of supply", "Reverse charge", "Invoice type", "Rate", "Taxable value", "IGST", "CGST", "SGST", "Cess"],
                            [(r["gstin"], r["name"], r["number"], r["date"].strftime("%d-%b-%y"), r["doc_total"], _pos(r["pos"]),
                              "N", "Regular", r["rate"], r["taxable"], r["igst"], r["cgst"], r["sgst"], 0) for r in rows])
    if table == "b2c":
        g = build_gstr1(s_lines)
        lines = [("B2C large", r["number"], r["date"].strftime("%d-%b-%y"), r["doc_total"], _pos(r["pos"]), r["rate"], r["taxable"], r["igst"], r["cgst"], r["sgst"]) for r in g["b2c_large"]]
        lines += [("B2C small", "", "", "", _pos(r["pos"]), r["rate"], r["taxable"], r["igst"], r["cgst"], r["sgst"]) for r in g["b2c_small"]]
        return csv_response(name, ["Type", "Invoice number", "Invoice date", "Invoice value", "Place of supply", "Rate",
                                   "Taxable value", "IGST", "CGST", "SGST"], lines)
    if table == "hsn":
        rows = build_gstr1(s_lines)["hsn"]
        return csv_response(name, ["HSN", "Description", "UQC", "Total quantity", "Rate", "Total value", "Taxable value", "IGST", "CGST", "SGST"],
                            [(r["hsn"], r["desc"], r["unit"], r["qty"], r["rate"], r["value"], r["taxable"], r["igst"], r["cgst"], r["sgst"]) for r in rows])
    if table == "gstr3b":
        opening, _ = parse_opening(request.GET)
        r = build_gstr3b(s_lines, purchase_lines(cid, p.start, p.end), opening)
        o, c, pay = r["outward"], r["credit"], r["payable"]
        lines = [("3.1(a)", "Outward taxable supplies (other than zero rated, nil rated, exempt)", o["taxable"], o["igst"], o["cgst"], o["sgst"]),
                 ("3.1(c)", "Other outward supplies (nil rated, exempt)", r["nil_value"], 0, 0, 0)]
        lines += [("3.2", f"Inter-state supplies to unregistered persons - {_pos(u['pos'])}", u["taxable"], u["igst"], 0, 0) for u in r["unreg"]]
        lines += [("4(A)(5)", "ITC on purchases from registered suppliers", "", r["itc"]["igst"], r["itc"]["cgst"], r["itc"]["sgst"]),
                  ("", "Credit brought forward", "", r["opening"]["igst"], r["opening"]["cgst"], r["opening"]["sgst"]),
                  ("6.1", "Tax payable in cash after using credit", "", pay["igst"], pay["cgst"], pay["sgst"]),
                  ("", "Credit left over", "", r["left"]["igst"], r["left"]["cgst"], r["left"]["sgst"])]
        return csv_response(name, ["Section", "Description", "Taxable value", "IGST", "CGST", "SGST"], lines)
    raise Http404
