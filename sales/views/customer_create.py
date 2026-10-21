from django.contrib import messages
from django.shortcuts import redirect, render

from core.parties import is_duplicate, parse_party_form
from core.permissions import area_required
from sales.models import Customer


@area_required("sales")
def customer_create(request):
    company = request.me.company
    v = {"name": "", "gstin": "", "address": "", "state": company.state, "phone": "", "email": ""}
    if request.method == "POST":
        v, errors = parse_party_form(request.POST, "Customer")
        if not errors and is_duplicate(Customer, company.id, v["name"], v["gstin"]):
            errors.append("A customer with this name and GSTIN already exists.")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            Customer.objects.create(company_id=company.id, **v)
            messages.success(request, "Customer saved.")
            return redirect("sales:customer_list")
    return render(request, "sales/customer_form.html", {"v": v, "customer": None})
