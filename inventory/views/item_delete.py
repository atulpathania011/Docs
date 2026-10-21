from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.permissions import area_required
from inventory.models import Item


@require_POST
@area_required("inventory")
def item_delete(request, pk):
    get_object_or_404(Item, pk=pk, company_id=request.me.company_id).delete()
    messages.success(request, "Item deleted. Invoices and purchases already made are not changed.")
    return redirect("inventory:item_list")
