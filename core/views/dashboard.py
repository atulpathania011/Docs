from django.shortcuts import render
from django.urls import reverse

from core.constants import AREAS
from core.navigation import area_url
from core.permissions import login_required

# Each statement sits directly under its project area on the home page.
STATEMENTS = {
    "sales": {"title": "Sales statement", "desc": "Every invoice for a period, with totals. Edit and print from here.",
              "url_name": "statements:sales", "needs": {"sales", "reports"}},
    "purchase": {"title": "Purchase statement", "desc": "Every purchase bill for a period, with totals. Edit and print from here.",
                 "url_name": "statements:purchases", "needs": {"purchase", "reports"}},
}


@login_required
def dashboard(request):
    mine = request.me.areas
    rows = []
    for key, info in AREAS.items():
        rows.append({"key": key, **info, "url": area_url(key), "allowed": key in mine, "child": False})
        if key in STATEMENTS:
            s = STATEMENTS[key]
            rows.append({"key": key + "-statement", "title": s["title"], "desc": s["desc"],
                         "url": reverse(s["url_name"]), "allowed": bool(mine & s["needs"]), "child": True})
    return render(request, "core/dashboard.html", {"rows": rows, "open_count": len(mine), "area_count": len(AREAS)})
