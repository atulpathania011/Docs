from .constants import AREAS, STATES, UNIT_OPTIONS


def globals(request):
    return {"me": getattr(request, "me", None), "AREAS": AREAS, "STATES": STATES, "UNIT_OPTIONS": UNIT_OPTIONS}
