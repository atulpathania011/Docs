from django.db import transaction
from django.utils import timezone

from core.documents import apply_cleaned, company_snapshot, make_items
from core.numbering import next_number
from core.parties import save_party_if_new
from inventory.services import save_items_if_new

from .models import Customer, Invoice, InvoiceItem


def create_invoice(company, me, cleaned, save_customer, save_items=False):
    """Raises IntegrityError if two people save at the same moment and get the same number."""
    with transaction.atomic(using="invoices"):
        inv = Invoice(company_id=company.id, company_snapshot=company_snapshot(company), created_by_id=me.id,
                      number=next_number(Invoice, company.id, cleaned["date"], "INV"))
        apply_cleaned(inv, cleaned)
        inv.save()
        InvoiceItem.objects.bulk_create(make_items(InvoiceItem, "invoice", inv, cleaned["items"]))
        if save_customer:
            save_party_if_new(Customer, company.id, cleaned)
    if save_items:                       # the item list is in its own database file
        save_items_if_new(company.id, cleaned["items"], "sale")
    return inv


def update_invoice(inv, me, cleaned, save_items=False):
    """The invoice number never changes. Items are replaced with what was submitted."""
    with transaction.atomic(using="invoices"):
        apply_cleaned(inv, cleaned)
        inv.updated_by_id = me.id
        inv.updated_at = timezone.now()
        inv.save()
        inv.items.all().delete()
        InvoiceItem.objects.bulk_create(make_items(InvoiceItem, "invoice", inv, cleaned["items"]))
    if save_items:
        save_items_if_new(inv.company_id, cleaned["items"], "sale")
    return inv
