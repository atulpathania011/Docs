from django.contrib import messages
from django.shortcuts import redirect, render

from core.constants import DEFAULT_GST
from core.documents import GST_OPTIONS
from core.permissions import area_required
from inventory.models import Item
from inventory.parse import parse_item_form


@area_required("inventory")
def item_create(request):
    v = {"name": "", "hsn": "", "unit": "", "gst": DEFAULT_GST, "sale_rate": "", "purchase_rate": ""}
    if request.method == "POST":
        v, clean, errors = parse_item_form(request.POST)
        cid = request.me.company_id
        if not errors and Item.objects.filter(company_id=cid, name__iexact=clean["name"]).exists():
            errors.append("An item with this name already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            Item.objects.create(company_id=cid, **clean)
            messages.success(request, "Item saved.")
            return redirect("inventory:item_list")
    return render(request, "inventory/item_form.html", {"v": v, "item": None, "gst_options": GST_OPTIONS})
