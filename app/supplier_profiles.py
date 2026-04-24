from __future__ import annotations

from typing import TypedDict


class SupplierProfile(TypedDict):
    display_name: str
    contact: str
    address: str


SUPPLIER_PROFILES: dict[str, SupplierProfile] = {
    "El Rodeo": {
        "display_name": "FLORES CORTEZ, S.A. DE C.V.",
        "contact": "76039558",
        "address": "Av. Roosevelt Sur #109-D, San Miguel Centro, San Miguel",
    },
    "Todito": {
        "display_name": "TODITO ALMACEN Y LIBRERIA SA DE CV",
        "contact": "2661-1506",
        "address": "2a Calle Pte. #205, San Miguel",
    },
    "Pricemart": {
        "display_name": "PriceSmart El Salvador, S.A. de C.V.",
        "contact": "(503) 2623-4000",
        "address": "Urb. San Andres, Carretera Panamericana, Km 133.5 Tramo Bypass y Ave. 2",
    },
    "Emma Bakery": {
        "display_name": "AGROINVERSIONES 4R, S.A. DE C.V. (EMMA BAKERY)",
        "contact": "+6454 7531",
        "address": "COL CIUDAD JARDIN, #1315, 3 CALLE PONIENTE, SAN MIGUEL",
    },
}


def get_supplier_profile(supplier_name: str) -> SupplierProfile:
    normalized = str(supplier_name or "").strip()
    profile = SUPPLIER_PROFILES.get(normalized)
    if profile:
        return {
            "display_name": profile.get("display_name") or normalized or "-",
            "contact": profile.get("contact") or "-",
            "address": profile.get("address") or "-",
        }
    return {
        "display_name": normalized or "-",
        "contact": "-",
        "address": "-",
    }
