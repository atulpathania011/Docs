from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.documents import (parse_document, party_values_from_doc, party_values_from_post,
                            rows_from_items, rows_from_post)
from core.permissions import area_required
from core.redirects import after_save, safe_next
from sales.form_context import invoice_form_context
from sales.models import Invoice
from sales.services import update_invoice


@area_required("sales")
def invoice_edit(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, company_id=request.me.company_id)
    # where to go afterwards: the statement the person came from (if any)
    next_url = safe_next(request.POST.get("next") if request.method == "POST" else request.GET.get("next"))
    if inv.is_cancelled:
        messages.error(request, "This invoice was cancelled earlier and cannot be edited.")
        return redirect(next_url) if next_url else redirect("sales:invoice_detail", pk=inv.pk)
    # tax type (CGST+SGST or IGST) is worked out against the company state the invoice was made with
    company_state = inv.company_snapshot.get("state") or request.me.company.state
    v, rows = party_values_from_doc(inv), rows_from_items(inv.items.all())
    if request.method == "POST":
        cleaned, errors = parse_document(request.POST, company_state, "Customer")
        if not errors:
            update_invoice(inv, request.me, cleaned, bool(request.POST.get("save_items")))
            messages.success(request, f"Invoice {inv.number} updated.")
            return after_save(request, "sales:invoice_detail", inv.pk, next_url)
        for e in errors:
            messages.error(request, e)
        v, rows = party_values_from_post(request.POST), rows_from_post(request.POST)
    return render(request, "sales/invoice_form.html", invoice_form_context(
        request, v=v, rows=rows, invoice=inv, company_state=company_state, next_url=next_url))
