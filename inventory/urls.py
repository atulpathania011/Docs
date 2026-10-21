from django.urls import path

from .views.item_create import item_create
from .views.item_delete import item_delete
from .views.item_edit import item_edit
from .views.item_list import item_list

app_name = "inventory"
urlpatterns = [
    path("", item_list, name="item_list"),
    path("new/", item_create, name="item_create"),
    path("<int:pk>/", item_edit, name="item_edit"),
    path("<int:pk>/delete/", item_delete, name="item_delete"),
]
