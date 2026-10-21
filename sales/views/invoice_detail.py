from django.shortcuts import get_object_or_404, render

from core.permissions import area_required
from core.redirects import safe_next
from directory.models import Profile
from sales.models import Invoice


@area_required("sales", "reports")
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, company_id=request.me.company_id)
    names = dict(Profile.objects.filter(pk__in=[i for i in (inv.created_by_id, inv.updated_by_id) if i])
                 .values_list("id", "full_name"))
    return render(request, "sales/invoice_detail.html", {
        "inv": inv, "items": inv.items.all(), "seller": inv.company_snapshot,
        "creator": names.get(inv.created_by_id, ""), "editor": names.get(inv.updated_by_id, ""),
        "can_edit": "sales" in request.me.areas,
        "next_url": safe_next(request.GET.get("next")), "autoprint": request.GET.get("print") == "1"})
