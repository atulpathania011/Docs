from django.urls import path

from .views.customer_create import customer_create
from .views.customer_delete import customer_delete
from .views.customer_edit import customer_edit
from .views.customer_list import customer_list
from .views.invoice_create import invoice_create
from .views.invoice_detail import invoice_detail
from .views.invoice_edit import invoice_edit
from .views.invoice_list import invoice_list

app_name = "sales"
urlpatterns = [
    path("", invoice_list, name="invoice_list"),
    path("new/", invoice_create, name="invoice_create"),
    path("customers/", customer_list, name="customer_list"),
    path("customers/new/", customer_create, name="customer_create"),
    path("customers/<int:pk>/", customer_edit, name="customer_edit"),
    path("customers/<int:pk>/delete/", customer_delete, name="customer_delete"),
    path("<int:pk>/", invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", invoice_edit, name="invoice_edit"),
]
