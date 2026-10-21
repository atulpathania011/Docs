from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.documents import GST_OPTIONS
from core.gst import plain
from core.permissions import area_required
from inventory.models import Item
from inventory.parse import parse_item_form


@area_required("inventory")
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk, company_id=request.me.company_id)
    v = {"name": item.name, "hsn": item.hsn, "unit": item.unit, "gst": plain(item.gst_rate),
         "sale_rate": plain(item.sale_rate) if item.sale_rate is not None else "",
         "purchase_rate": plain(item.purchase_rate) if item.purchase_rate is not None else ""}
    if request.method == "POST":
        v, clean, errors = parse_item_form(request.POST)
        if not errors and Item.objects.filter(company_id=item.company_id, name__iexact=clean["name"]).exclude(pk=item.pk).exists():
            errors.append("An item with this name already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            for k, val in clean.items():
                setattr(item, k, val)
            item.save()
            messages.success(request, "Item saved. Invoices and purchases already made are not changed.")
            return redirect("inventory:item_list")
    return render(request, "inventory/item_form.html", {"v": v, "item": item, "gst_options": GST_OPTIONS})
