from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.permissions import area_required
from sales.models import Customer


@require_POST
@area_required("sales")
def customer_delete(request, pk):
    get_object_or_404(Customer, pk=pk, company_id=request.me.company_id).delete()
    messages.success(request, "Customer deleted. Existing invoices are not affected.")
    return redirect("sales:customer_list")
