from django.db.models import Q
from django.shortcuts import render

from core.permissions import area_required
from sales.models import Invoice


@area_required("sales")
def invoice_list(request):
    q = request.GET.get("q", "").strip()[:60]
    qs = Invoice.objects.filter(company_id=request.me.company_id)
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(party_name__icontains=q) | Q(party_gstin__icontains=q))
    return render(request, "sales/invoice_list.html", {
        "invoices": qs[:100], "q": q, "company_ready": request.me.company.ready})
