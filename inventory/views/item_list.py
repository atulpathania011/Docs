from django.db.models import Q
from django.shortcuts import render

from core.gst import plain
from core.permissions import area_required
from inventory.models import Item


@area_required("inventory")
def item_list(request):
    q = request.GET.get("q", "").strip()[:60]
    qs = Item.objects.filter(company_id=request.me.company_id)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(hsn__icontains=q))
    rows = [{"item": i, "gst": plain(i.gst_rate), "sale": plain(i.sale_rate) if i.sale_rate is not None else "",
             "purchase": plain(i.purchase_rate) if i.purchase_rate is not None else ""} for i in qs[:500]]
    return render(request, "inventory/item_list.html", {"rows": rows, "q": q})
