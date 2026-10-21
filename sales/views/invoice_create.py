from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render

from core.documents import blank_row, parse_document, party_values_from_post, rows_from_post
from core.permissions import area_required
from core.redirects import after_save
from sales.form_context import default_values, invoice_form_context
from sales.services import create_invoice


@area_required("sales")
def invoice_create(request):
    company = request.me.company
    if not company.ready:
        messages.error(request, "Add your company name and GSTIN before creating invoices.")
        return redirect("sales:invoice_list")
    v, rows = default_values(company.state), [blank_row()]
    if request.method == "POST":
        cleaned, errors = parse_document(request.POST, company.state, "Customer")
        if not errors:
            try:
                inv = create_invoice(company, request.me, cleaned, bool(request.POST.get("save_party")),
                                     bool(request.POST.get("save_items")))
            except IntegrityError:
                errors = ["Another invoice was saved at the same moment. Click Save invoice again."]
            else:
                messages.success(request, f"Invoice {inv.number} saved.")
                return after_save(request, "sales:invoice_detail", inv.pk, "")
        for e in errors:
            messages.error(request, e)
        v, rows = party_values_from_post(request.POST), rows_from_post(request.POST)
    return render(request, "sales/invoice_form.html",
                  invoice_form_context(request, v=v, rows=rows, company_state=company.state))
