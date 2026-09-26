"""Orquesta todo el proceso. Lo usan tanto la CLI (main.py) como la app web (app.py)."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.exporter import build_filename, export_to_excel
from src.normalize import (
    classify_website,
    clean_social_url,
    clean_website,
    normalize_phone,
    score_business,
    social_network_of,
)
from src.scraper import Cancelled, GoogleMapsScraper
from src.social_scraper import analyze_website, empty_result


DEFAULTS = {
    "tipo": "",
    "ubicacion": "",
    "zonas": [],
    "max_resultados": 0,       # 0 = sin límite (hasta que se acabe la lista)
    "concurrencia": 3,
    "headless": True,
    "analizar_webs": True,
    "pais": "51",
    "rating_min": 0,
    "resenas_min": 0,
    "solo_con_telefono": False,
    "solo_sin_web": False,
    "excluir_cerrados": True,
    "radio_km": 0,             # 0 = automático según el tamaño de la ubicación
}


def _split(value):
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value or "").replace("\n", ",").split(",")
    return [item.strip() for item in items if item and item.strip()]


def build_queries(params):
    types = _split(params["tipo"])
    zones = _split(params.get("zonas"))
    location = params["ubicacion"].strip()
    queries = []
    for business_type in types:
        for area in ([f"{zone}, {location}" for zone in zones] or [location]):
            queries.append({"texto": f"{business_type} en {area}", "area": area})
    return queries


def business_key(business):
    return business.get("place_id") or f"{business.get('nombre', '')}|{business.get('direccion', '')}"


def prepare(business, country):
    """Normaliza un negocio recién extraído (antes del análisis web)."""

    raw_phone = business.pop("telefono_raw", "")
    phone, kind, whatsapp = normalize_phone(raw_phone, country)
    # "Teléfono" queda tal como lo muestra Google (formato local); el internacional va aparte.
    business["telefono"] = raw_phone.strip()
    business["telefono_intl"] = phone
    business["tipo_telefono"] = kind
    business["whatsapp"] = whatsapp
    site = clean_website(business.get("sitio_web", ""))
    if social_network_of(site):
        site = clean_social_url(site) or site
    business["sitio_web"] = site
    for key, value in empty_result(business["sitio_web"]).items():
        business.setdefault(key, value)
    business["tipo_web"] = classify_website(business["sitio_web"])
    rescore(business)
    return business


def rescore(business):
    score, priority, reasons = score_business(business)
    business["lead_score"] = score
    business["prioridad"] = priority
    business["motivos"] = reasons


def merge_web(business, web):
    for key, value in web.items():
        if key == "whatsapp_web":
            if value and not business.get("whatsapp"):
                business["whatsapp"] = value
            continue
        if value or key not in business:
            business[key] = value
    rescore(business)


def describe_filters(params):
    parts = []
    if params["rating_min"]:
        parts.append(f"rating ≥ {params['rating_min']}")
    if params["resenas_min"]:
        parts.append(f"reseñas ≥ {params['resenas_min']}")
    if params["solo_con_telefono"]:
        parts.append("solo con teléfono")
    if params["solo_sin_web"]:
        parts.append("solo sin web propia")
    if params["excluir_cerrados"]:
        parts.append("sin cerrados")
    if params["max_resultados"]:
        parts.append(f"máx. {params['max_resultados']} por búsqueda")
    if params["radio_km"]:
        parts.append(f"radio {params['radio_km']} km")
    return ", ".join(parts) or "Ninguno"


def apply_filters(businesses, params):
    kept, discarded = [], []
    for b in businesses:
        reason = ""
        if params["excluir_cerrados"] and b.get("estado_negocio", "").startswith("Cerrado"):
            reason = b["estado_negocio"]
        elif params["rating_min"] and (b.get("rating") or 0) < float(params["rating_min"]):
            reason = "Rating bajo"
        elif params["resenas_min"] and (b.get("resenas") or 0) < int(params["resenas_min"]):
            reason = "Pocas reseñas"
        elif params["solo_con_telefono"] and not b.get("telefono"):
            reason = "Sin teléfono"
        elif params["solo_sin_web"] and b.get("tipo_web") == "Web propia":
            reason = "Tiene web propia"
        if reason:
            b["motivos"] = f"Descartado: {reason}"
            discarded.append(b)
        else:
            kept.append(b)
    return kept, discarded


def run_job(raw_params, emit=None, is_cancelled=None):
    """Ejecuta la búsqueda completa. Devuelve dict con ruta del Excel y resumen.

    emit(kind, **data) recibe eventos de progreso: phase, log, scroll, cards,
    business, web, done.
    """

    emit = emit or (lambda kind, **data: None)
    is_cancelled = is_cancelled or (lambda: False)
    params = {**DEFAULTS, **{k: v for k, v in raw_params.items() if v is not None}}
    params["zonas"] = _split(params["zonas"])
    queries = build_queries(params)
    params["queries"] = [q["texto"] for q in queries]
    params["filtros_texto"] = describe_filters(params)

    if not queries:
        raise ValueError("Indica el tipo de negocio y la ubicación.")

    started = time.time()
    businesses = {}
    interrupted = ""

    def on_scraper_event(kind, **data):
        if kind == "business":
            business = prepare(data["business"], params["pais"])
            businesses[business_key(business)] = business
            emit("business", business=business, key=business_key(business),
                 done=data["done"], total=data["total"])
        else:
            emit(kind, **data)

    # 1) Google Maps
    scraper = GoogleMapsScraper(
        headless=params["headless"],
        concurrency=params["concurrencia"],
        on_event=on_scraper_event,
        is_cancelled=is_cancelled,
        radius_km=float(params["radio_km"] or 0),
    )
    try:
        scraper.run(queries, max_results=int(params["max_resultados"] or 0),
                    location=params["ubicacion"])
    except Cancelled:
        interrupted = "Detenido por el usuario"
        emit("log", message="Búsqueda detenida: se guardará lo obtenido hasta ahora.", level="warn")
    except Exception as error:
        interrupted = f"Error: {error}"
        emit("log", message=f"La búsqueda se cortó ({str(error)[:120]}). Se guarda lo obtenido.",
             level="error")

    items = list(businesses.values())
    if scraper.center:
        params["centro"] = {"lat": scraper.center[0], "lng": scraper.center[1],
                            "radio_km": scraper.center[2]}

    # Resultados que Google mostró pero están fuera de la zona buscada.
    out_of_area = []
    for card in scraper.out_of_area:
        out_of_area.append(prepare({
            "nombre": card["nombre_lista"],
            "categoria": card["lista_categoria"],
            "rating": card["lista_rating"],
            "resenas": card["lista_resenas"],
            "lat": card["lat"],
            "lng": card["lng"],
            "place_id": card["place_id"],
            "busqueda": card.get("busqueda", ""),
            "distancia_km": card.get("distancia_km"),
            "google_maps": card["url"].split("?")[0],
        }, params["pais"]))

    # 2) Sitios web (redes, emails, estado)
    if params["analizar_webs"] and items and not interrupted:
        with_site = [b for b in items if b.get("sitio_web")]
        emit("phase", phase="webs", message=f"Revisando {len(with_site)} sitios web")
        done = 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(analyze_website, b["sitio_web"]): b for b in with_site}
            for future in as_completed(futures):
                business = futures[future]
                try:
                    merge_web(business, future.result())
                except Exception:
                    pass
                done += 1
                emit("web", business=business, key=business_key(business),
                     done=done, total=len(with_site))
                if is_cancelled():
                    interrupted = "Detenido por el usuario"
                    for pending in futures:
                        pending.cancel()
                    break

    # 3) Filtros, orden y Excel
    emit("phase", phase="excel", message="Generando Excel")
    kept, discarded = apply_filters(items, params)
    for business in out_of_area:
        business["motivos"] = f"Descartado: fuera de la zona ({business['distancia_km']} km del centro)"
        business["prioridad"] = "Descartar"
        business["lead_score"] = 0
    discarded.extend(out_of_area)
    kept.sort(key=lambda b: (-b.get("lead_score", 0), -(b.get("resenas") or 0)))
    for index, business in enumerate(kept, start=1):
        business["n"] = index
    for index, business in enumerate(discarded, start=1):
        business["n"] = index

    elapsed = int(time.time() - started)
    stats = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "duracion": f"{elapsed // 60} min {elapsed % 60} s",
        "segundos": elapsed,
        "encontrados": len(items),
        "descartados": len(discarded),
        "interrumpido": interrupted,
    }

    basename = build_filename(_split(params["tipo"])[0] if _split(params["tipo"]) else "negocios",
                              params["ubicacion"])
    if interrupted:
        basename += "_parcial"

    path, summary = export_to_excel(
        kept,
        params["tipo"],
        params["ubicacion"],
        params=params,
        stats=stats,
        discarded=discarded,
        basename=basename,
    )

    result = {"excel": path, "summary": summary, "stats": stats, "params": params,
              "businesses": kept, "discarded": discarded}
    emit("done", **result)
    return result
