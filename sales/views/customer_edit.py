from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.parties import is_duplicate, parse_party_form
from core.permissions import area_required
from sales.models import Customer


@area_required("sales")
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company_id=request.me.company_id)
    v = {k: getattr(customer, k) for k in ("name", "gstin", "address", "state", "phone", "email")}
    if request.method == "POST":
        v, errors = parse_party_form(request.POST, "Customer")
        if not errors and is_duplicate(Customer, customer.company_id, v["name"], v["gstin"], exclude_pk=customer.pk):
            errors.append("A customer with this name and GSTIN already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            for k, val in v.items():
                setattr(customer, k, val)
            customer.save()
            messages.success(request, "Customer saved.")
            return redirect("sales:customer_list")
    return render(request, "sales/customer_form.html", {"v": v, "customer": customer})
