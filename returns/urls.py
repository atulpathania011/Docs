from django.urls import path

from .views.export_csv import export_csv
from .views.gstr1 import gstr1
from .views.gstr3b import gstr3b
from .views.returns_home import returns_home

app_name = "returns"
urlpatterns = [
    path("", returns_home, name="home"),
    path("gstr1/", gstr1, name="gstr1"),
    path("gstr3b/", gstr3b, name="gstr3b"),
    path("export/<str:table>/", export_csv, name="export"),
]
