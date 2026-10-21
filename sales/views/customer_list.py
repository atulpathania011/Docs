from django.db.models import Q
from django.shortcuts import render

from core.permissions import area_required
from sales.models import Customer


@area_required("sales")
def customer_list(request):
    q = request.GET.get("q", "").strip()[:60]
    qs = Customer.objects.filter(company_id=request.me.company_id)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(gstin__icontains=q) | Q(phone__icontains=q))
    return render(request, "sales/customer_list.html", {"rows": qs[:500], "q": q})
