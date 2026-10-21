from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.permissions import area_required
from sales.models import Invoice


@require_POST
@area_required("sales")
def invoice_cancel(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, company_id=request.me.company_id)
    if not inv.is_cancelled:
        inv.status = "cancelled"
        inv.updated_by_id, inv.updated_at = request.me.id, timezone.now()
        inv.save()
        messages.success(request, f"Invoice {inv.number} cancelled.")
    return redirect("sales:invoice_detail", pk=inv.pk)
