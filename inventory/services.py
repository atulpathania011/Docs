from core.gst import plain

from .models import Item


def item_choices(company_id, kind):
    """The item list shaped for the invoice/purchase form's pop-up. kind is 'sale' or 'purchase'."""
    out = []
    for it in Item.objects.filter(company_id=company_id).order_by("name"):
        rate = it.sale_rate if kind == "sale" else it.purchase_rate
        hint = [f"HSN {it.hsn}"] if it.hsn else []
        if it.unit:
            hint.append(it.unit)
        hint.append(f"{plain(it.gst_rate)}%")
        if rate is not None:
            hint.append(f"\u20b9{plain(rate)}")
        out.append({"name": it.name, "hsn": it.hsn, "unit": it.unit, "gst": plain(it.gst_rate),
                    "rate": plain(rate) if rate is not None else "", "hint": " \u00b7 ".join(hint)})
    return out


def save_items_if_new(company_id, lines, kind):
    """Add items typed on a document to the item list (existing names are left alone)."""
    seen = set()
    for line in lines:
        name = line["description"]
        if name.lower() in seen or Item.objects.filter(company_id=company_id, name__iexact=name).exists():
            continue
        seen.add(name.lower())
        Item.objects.create(company_id=company_id, name=name, hsn=line["hsn"], unit=line["unit"],
                            gst_rate=line["gst_rate"],
                            **{"sale_rate" if kind == "sale" else "purchase_rate": line["rate"]})
