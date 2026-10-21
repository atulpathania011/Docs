"""GSTR-1 and GSTR-3B working summaries, built from the saved invoices and purchases.

These are SUMMARIES to help prepare a return. They are not filed from here.
Not covered: credit/debit notes, exports, reverse charge, ITC eligibility rules, composition dealers, cess.
"""
from collections import defaultdict
from decimal import Decimal

from core.gst import money
from purchases.models import PurchaseItem
from sales.models import Invoice, InvoiceItem

ZERO = Decimal("0")
B2C_LARGE_LIMIT = Decimal("250000")      # inter-state invoice to an unregistered person above this value


def split_tax(tax, supply_type):
    """(igst, cgst, sgst) for one line."""
    if supply_type == "intra":
        cgst = money(tax / 2)
        return ZERO, cgst, tax - cgst
    return tax, ZERO, ZERO


def _line(doc, it):
    igst, cgst, sgst = split_tax(it.tax, doc.supply_type)
    return {"doc_id": doc.id, "date": doc.date, "number": doc.number, "gstin": doc.party_gstin,
            "name": doc.party_name, "pos": doc.state_code, "supply": doc.supply_type, "doc_total": doc.total,
            "bill_number": getattr(doc, "bill_number", ""), "desc": it.description, "hsn": it.hsn,
            "unit": it.unit, "qty": it.qty, "rate": it.gst_rate, "taxable": it.taxable, "tax": it.tax,
            "igst": igst, "cgst": cgst, "sgst": sgst}


def sales_lines(company_id, start, end):
    qs = (InvoiceItem.objects.filter(invoice__company_id=company_id, invoice__status="active",
                                     invoice__date__range=(start, end))
          .select_related("invoice").order_by("invoice__date", "invoice_id", "id"))
    return [_line(it.invoice, it) for it in qs]


def purchase_lines(company_id, start, end):
    qs = (PurchaseItem.objects.filter(purchase__company_id=company_id, purchase__status="active",
                                      purchase__date__range=(start, end))
          .select_related("purchase").order_by("purchase__date", "purchase_id", "id"))
    return [_line(it.purchase, it) for it in qs]


def _zero():
    return {"taxable": ZERO, "igst": ZERO, "cgst": ZERO, "sgst": ZERO}


def _add(acc, line):
    for k in ("taxable", "igst", "cgst", "sgst"):
        acc[k] += line[k]


def invoice_documents(company_id, start, end):
    """Table 13: how many invoices were issued, first and last number, and how many were cancelled."""
    invs = list(Invoice.objects.filter(company_id=company_id, date__range=(start, end)).order_by("id"))
    return {"count": len(invs), "cancelled": sum(1 for i in invs if i.is_cancelled),
            "first": invs[0].number if invs else "", "last": invs[-1].number if invs else ""}


def build_gstr1(lines):
    b2b, b2c_large, b2c_small, hsn = {}, {}, {}, {}
    nil = defaultdict(lambda: ZERO)
    totals = _zero()
    for l in lines:
        rate = l["rate"]
        if rate == 0:        # nil-rated / exempt items go to Table 8, not to tables 4 and 7
            nil[(l["supply"], bool(l["gstin"]))] += l["taxable"]
        else:
            _add(totals, l)
            if l["gstin"]:
                row = b2b.setdefault((l["doc_id"], rate), {**_zero(), "gstin": l["gstin"], "name": l["name"],
                                     "number": l["number"], "date": l["date"], "pos": l["pos"],
                                     "doc_total": l["doc_total"], "rate": rate})
                _add(row, l)
            elif l["supply"] == "inter" and l["doc_total"] > B2C_LARGE_LIMIT:
                row = b2c_large.setdefault((l["doc_id"], rate), {**_zero(), "number": l["number"], "date": l["date"],
                                           "pos": l["pos"], "doc_total": l["doc_total"], "rate": rate})
                _add(row, l)
            else:
                row = b2c_small.setdefault((l["pos"], rate), {**_zero(), "pos": l["pos"], "rate": rate})
                _add(row, l)
        h = hsn.setdefault((l["hsn"], l["unit"], rate), {**_zero(), "hsn": l["hsn"], "unit": l["unit"], "rate": rate,
                           "desc": l["desc"], "qty": ZERO})
        h["qty"] += l["qty"]
        _add(h, l)
    for h in hsn.values():
        h["value"] = h["taxable"] + h["igst"] + h["cgst"] + h["sgst"]
    nil_rows = [{"supply": s, "registered": r, "taxable": v} for (s, r), v in sorted(nil.items())]
    return {
        "b2b": sorted(b2b.values(), key=lambda r: (r["date"], r["number"], r["rate"])),
        "b2c_large": sorted(b2c_large.values(), key=lambda r: (r["date"], r["number"], r["rate"])),
        "b2c_small": sorted(b2c_small.values(), key=lambda r: (r["pos"], r["rate"])),
        "nil": nil_rows, "nil_total": sum((r["taxable"] for r in nil_rows), ZERO),
        "hsn": sorted(hsn.values(), key=lambda r: (r["hsn"], r["unit"], r["rate"])),
        "totals": {**totals, "tax": totals["igst"] + totals["cgst"] + totals["sgst"]},
        "invoice_count": len({l["doc_id"] for l in lines}),
    }


def set_off(liability, credit):
    """Use the credit to reduce the tax payable, in the order the GST rules allow.

    IGST credit goes first against IGST, then CGST, then SGST.
    CGST credit goes against CGST, then IGST (never SGST).  SGST credit goes against SGST, then IGST (never CGST).
    Returns (tax payable in cash, credit left over)."""
    liab, cred = dict(liability), dict(credit)
    for head, targets in (("igst", ("igst", "cgst", "sgst")), ("cgst", ("cgst", "igst")), ("sgst", ("sgst", "igst"))):
        for t in targets:
            use = min(cred[head], liab[t])
            cred[head] -= use
            liab[t] -= use
    return liab, cred


def build_gstr3b(s_lines, p_lines, opening):
    outward, nil_value, unreg = _zero(), ZERO, {}
    for l in s_lines:
        if l["rate"] == 0:
            nil_value += l["taxable"]
            continue
        _add(outward, l)
        if not l["gstin"] and l["supply"] == "inter":          # Table 3.2: to unregistered persons, by state
            _add(unreg.setdefault(l["pos"], {**_zero(), "pos": l["pos"]}), l)
    itc, no_itc_tax = {"igst": ZERO, "cgst": ZERO, "sgst": ZERO}, ZERO
    for l in p_lines:
        if l["gstin"]:                                          # only bills from registered suppliers carry credit
            for h in itc:
                itc[h] += l[h]
        else:
            no_itc_tax += l["tax"]
    liability = {h: outward[h] for h in ("igst", "cgst", "sgst")}
    credit = {h: itc[h] + opening[h] for h in itc}
    payable, left = set_off(liability, credit)
    return {"outward": outward, "nil_value": nil_value, "unreg": sorted(unreg.values(), key=lambda r: r["pos"]),
            "itc": itc, "opening": opening, "credit": credit, "payable": payable, "left": left,
            "payable_total": sum(payable.values(), ZERO), "no_itc_tax": no_itc_tax,
            "out_tax": sum(liability.values(), ZERO), "itc_total": sum(itc.values(), ZERO)}
