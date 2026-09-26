"""Extracción de negocios desde Google Maps con Playwright (asíncrono).

Flujo:
  1. Abre la búsqueda en Google Maps (en español).
  2. Hace scroll en la lista hasta cargar todos los resultados.
  3. Lee rating/reseñas desde las tarjetas de la lista.
  4. Visita cada ficha en paralelo (varias pestañas) y extrae el detalle.
"""

import asyncio
import math
import random
import re
from urllib.parse import quote, urlparse, parse_qs, unquote

from playwright.async_api import async_playwright


MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}?hl=es"
MAPS_SEARCH_AT_URL = "https://www.google.com/maps/search/{query}/@{lat},{lng},{zoom}z?hl=es"


def distance_km(lat1, lng1, lat2, lng2):
    """Distancia en km entre dos coordenadas (haversine)."""

    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def radius_for_zoom(zoom):
    """Radio razonable según lo grande que es la zona (el zoom con que Maps la muestra)."""

    if zoom <= 7:
        return 300
    return {8: 200, 9: 120, 10: 60, 11: 35, 12: 25, 13: 15}.get(int(zoom), 12)

END_OF_LIST_TEXTS = (
    "Has llegado al final de la lista",
    "You've reached the end of the list",
)


class Cancelled(Exception):
    pass


# JS que lee las tarjetas de la lista de resultados.
CARDS_JS = """
() => [...document.querySelectorAll('div[role=feed] a[href*="/maps/place/"]')].map(a => ({
    url: a.href,
    nombre: a.getAttribute('aria-label') || '',
    texto: (a.parentElement ? a.parentElement.innerText : '').slice(0, 600)
}))
"""

# JS que lee toda la ficha de un negocio de una sola vez.
DETAIL_JS = r"""
() => {
  const main = document.querySelector('div[role=main][aria-label]') || document.querySelector('div[role=main]') || document.body;
  const h1 = main.querySelector('h1') || document.querySelector('h1');
  const items = [...main.querySelectorAll('[data-item-id]')].map(e => ({
      id: e.getAttribute('data-item-id') || '',
      aria: e.getAttribute('aria-label') || '',
      href: e.href || e.getAttribute('href') || '',
      txt: (e.innerText || '').trim()
  }));
  const arias = [...main.querySelectorAll('[aria-label]')].map(e => e.getAttribute('aria-label') || '');
  const cat = main.querySelector('button[jsaction*="category"]');
  const f7 = main.querySelector('.F7nice');
  // La tabla de horario es la que tiene días de la semana (la otra es la de reseñas).
  const days = /lunes|martes|miércoles|jueves|viernes|sábado|domingo/i;
  const table = [...main.querySelectorAll('table')].find(t => days.test(t.innerText));
  const hours = table ? [...table.querySelectorAll('tr')].map(tr =>
      [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/[\ue000-\uf8ff]/g, '').replace(/\s+/g, ' ').trim())
        .filter(Boolean).join(' ')
  ).filter(Boolean) : [];
  return {
    nombre: h1 ? h1.innerText.trim() : '',
    categoria: cat ? cat.innerText.trim() : '',
    f7: f7 ? f7.innerText : '',
    items: items,
    arias: arias.filter(t => t && t.length < 300),
    horario: hours,
    texto: (main.innerText || '').slice(0, 4000)
  };
}
"""


def _parse_number(text):
    if not text:
        return None
    text = text.strip().replace(" ", "")
    if re.fullmatch(r"\d+,\d", text):
        return float(text.replace(",", "."))
    if re.fullmatch(r"\d+\.\d", text):
        return float(text)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")


def _clean_text(text):
    return re.sub(r"\s+", " ", PRIVATE_USE.sub("", text or "").replace("\u202f", " ")).strip()


def parse_card(card):
    """Rating, reseñas, categoría y estado a partir del texto de la tarjeta."""

    text = PRIVATE_USE.sub("", card.get("texto", ""))
    data = {"rating": None, "resenas": None, "categoria": "", "cerrado": ""}

    match = re.search(r"(\d[,.]\d)\s*\(([\d.,\s]+)\)", text)
    if match:
        data["rating"] = _parse_number(match.group(1))
        data["resenas"] = _parse_number(match.group(2))
    else:
        match = re.search(r"^(\d[,.]\d)$", text, re.M)
        if match:
            data["rating"] = _parse_number(match.group(1))

    for line in text.splitlines():
        if "·" in line and not re.search(r"\d[,.]\d\s*\(", line):
            first = line.split("·")[0].strip()
            if first and not re.search(r"(Abierto|Cerrado|Abre|Cierra)", first):
                data["categoria"] = first
                break

    if "Cerrado permanentemente" in text:
        data["cerrado"] = "Cerrado permanentemente"
    elif "Cerrado temporalmente" in text:
        data["cerrado"] = "Cerrado temporalmente"

    return data


def place_ids_from_url(url):
    """(place_id ChIJ..., id interno 0x..:0x.., lat, lng) desde una URL de Maps."""

    place_id = ""
    match = re.search(r"!19s(ChIJ[\w-]+)", url)
    if match:
        place_id = match.group(1)
    cid = ""
    match = re.search(r"!1s(0x[0-9a-f]+:0x[0-9a-f]+)", url)
    if match:
        cid = match.group(1)
    lat = lng = None
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
    return place_id, cid, lat, lng


DAY_ORDER = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def format_hours(rows):
    """["sábado 10 a. m.–9 p. m.", ...] -> "Lun 10 a. m.–9 p. m. | Mar ..." (de lunes a domingo)."""

    if isinstance(rows, str):
        return rows
    by_day = {}
    for row in rows:
        match = re.match(r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s*(.*)", row, re.I)
        if match:
            by_day[match.group(1).lower()] = match.group(2).strip() or "—"
    if not by_day:
        return ""
    values = [by_day.get(day, "") for day in DAY_ORDER]
    if all(v == values[0] for v in values) and values[0]:
        return f"Todos los días {values[0]}"
    return " | ".join(f"{day[:3].capitalize()} {by_day[day]}" for day in DAY_ORDER if day in by_day)


def _unwrap_google_redirect(url):
    if "google." in url and "/url?" in url:
        target = parse_qs(urlparse(url).query).get("q", [""])[0]
        return unquote(target) if target else url
    return url


def parse_detail(raw):
    """Convierte la lectura cruda de la ficha en campos limpios."""

    data = {
        "nombre": _clean_text(raw.get("nombre", "")),
        "categoria": _clean_text(raw.get("categoria", "")),
        "direccion": "",
        "plus_code": "",
        "telefono_raw": "",
        "sitio_web": "",
        "horario": format_hours(raw.get("horario") or []),
        "perfil_reclamado": "Sí",
        "rating": None,
        "resenas": None,
        "estado_negocio": "",
    }

    for item in raw.get("items", []):
        item_id = item["id"]
        aria = item["aria"].strip()
        value = aria.split(":", 1)[1].strip() if ":" in aria else item["txt"]

        value = _clean_text(value)

        if item_id == "address":
            data["direccion"] = value
        elif item_id.startswith("phone:tel:"):
            data["telefono_raw"] = value or item_id.split("phone:tel:", 1)[1]
        elif item_id == "authority":
            data["sitio_web"] = _unwrap_google_redirect(item["href"])
        elif item_id == "oloc":
            data["plus_code"] = value
        elif item_id == "merchant":
            data["perfil_reclamado"] = "No"

    f7 = raw.get("f7", "")
    match = re.search(r"(\d[,.]\d)", f7)
    if match:
        data["rating"] = _parse_number(match.group(1))
    match = re.search(r"\(([\d.,\s]+)\)", f7)
    if match:
        data["resenas"] = _parse_number(match.group(1))

    for aria in raw.get("arias", []):
        if data["resenas"] is None:
            match = re.fullmatch(r"([\d.,\s]+)\s+reseñas?", aria.strip())
            if match:
                data["resenas"] = _parse_number(match.group(1))

    text = raw.get("texto", "")
    if "Cerrado permanentemente" in text:
        data["estado_negocio"] = "Cerrado permanentemente"
    elif "Cerrado temporalmente" in text:
        data["estado_negocio"] = "Cerrado temporalmente"
    else:
        data["estado_negocio"] = "Operativo"

    return data


class GoogleMapsScraper:

    def __init__(self, headless=True, concurrency=3, on_event=None, is_cancelled=None,
                 radius_km=0):
        self.headless = headless
        self.radius_km = radius_km      # 0 = automático según el tamaño de la ubicación
        self.center = None              # (lat, lng, radio_km) de la ubicación principal
        self.out_of_area = []           # resultados descartados por estar lejos
        self.concurrency = max(1, min(int(concurrency), 6))
        self.on_event = on_event or (lambda kind, **data: None)
        self.is_cancelled = is_cancelled or (lambda: False)

    def _check(self):
        if self.is_cancelled():
            raise Cancelled()

    def log(self, message, level="info"):
        self.on_event("log", message=message, level=level)

    # ------------------------------------------------------------------ public

    def run(self, queries, max_results=0, location=""):
        """queries: lista de {"texto": "barberías en Castilla, Piura", "area": "Castilla, Piura"}.

        max_results=0 significa sin límite: se detiene cuando se acaba la lista.
        """
        return asyncio.run(self._run(queries, max_results, location))

    async def _run(self, queries, max_results, location):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                locale="es-PE",
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
            )
            try:
                page = await context.new_page()

                # 0) Ubicar la zona en el mapa para anclar las búsquedas ahí.
                self.on_event("phase", phase="lista", message=f"Ubicando «{location}» en el mapa",
                              query_index=0, query_total=len(queries))
                center = await self._resolve_center(page, location) if location else None
                if center:
                    radius = self.radius_km or radius_for_zoom(center[2])
                    self.center = (center[0], center[1], radius)
                    self.log(f"Zona: {location} ({center[0]:.4f}, {center[1]:.4f}) · radio {radius} km")
                else:
                    self.log(f"No se pudo ubicar «{location}» en el mapa; no se filtrará por distancia.",
                             "warn")

                # 1) Recolectar tarjetas de todas las búsquedas.
                cards = {}
                area_centers = {}
                for index, query in enumerate(queries, start=1):
                    self._check()
                    text, area = query["texto"], query.get("area", "")
                    self.on_event("phase", phase="lista", message=f"Buscando: {text}",
                                  query_index=index, query_total=len(queries))

                    anchor = center
                    if area and area != location and self.center:
                        if area not in area_centers:
                            area_centers[area] = await self._resolve_center(page, area)
                        zone = area_centers[area]
                        if zone and distance_km(zone[0], zone[1], center[0], center[1]) <= self.center[2] * 1.5:
                            anchor = zone
                        elif zone:
                            self.log(f"«{area}» se ubicó lejos de {location}; se busca en el centro de {location}.",
                                     "warn")

                    found = await self._collect_cards(page, text, max_results, anchor)
                    new = away = 0
                    for card in found:
                        key = card["place_id"] or card["cid"] or card["url"].split("?")[0]
                        if key in cards:
                            continue
                        card["busqueda"] = text
                        if self.center and card["lat"] is not None:
                            km = distance_km(card["lat"], card["lng"], self.center[0], self.center[1])
                            card["distancia_km"] = round(km, 1)
                            if km > self.center[2]:
                                away += 1
                                self.out_of_area.append(card)
                                cards[key] = None
                                continue
                        cards[key] = card
                        new += 1
                    extra = f", {away} fuera de la zona" if away else ""
                    self.log(f"«{text}»: {len(found)} resultados ({new} nuevos{extra})")
                await page.close()

                cards = {k: v for k, v in cards.items() if v}

                cards = list(cards.values())
                self.on_event("cards", total=len(cards))
                if not cards:
                    return []

                # 2) Detalle de cada negocio en paralelo.
                self.on_event("phase", phase="detalle",
                              message=f"Analizando {len(cards)} negocios")
                return await self._scrape_details(context, cards)
            finally:
                await context.close()
                await browser.close()

    # ------------------------------------------------------------- list phase

    async def _resolve_center(self, page, place):
        """(lat, lng, zoom) de un lugar según Google Maps, o None."""

        try:
            await page.goto(MAPS_SEARCH_URL.format(query=quote(place)),
                            wait_until="domcontentloaded", timeout=45000)
            await self._accept_consent(page)
            for _ in range(24):
                match = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+),(\d+(?:\.\d+)?)z", page.url)
                if match:
                    lat, lng, zoom = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    # Si Maps abrió una ficha, el punto exacto está en !3d/!4d.
                    _, _, plat, plng = place_ids_from_url(page.url)
                    if plat is not None:
                        lat, lng = plat, plng
                    return lat, lng, zoom
                await page.wait_for_timeout(500)
        except Exception as error:
            self.log(f"Error ubicando «{place}»: {str(error)[:80]}", "warn")
        return None

    async def _collect_cards(self, page, query, max_results, anchor=None):
        if anchor:
            url = MAPS_SEARCH_AT_URL.format(query=quote(query), lat=anchor[0], lng=anchor[1],
                                            zoom=int(max(12, min(anchor[2], 15))))
        else:
            url = MAPS_SEARCH_URL.format(query=quote(query))
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await self._accept_consent(page)

        feed = page.locator('div[role="feed"]')
        try:
            await feed.wait_for(timeout=15000)
        except Exception:
            # Google abrió directamente una ficha (un único resultado).
            if "/maps/place/" in page.url:
                name = ""
                try:
                    name = (await page.locator("h1").first.inner_text(timeout=5000)).strip()
                except Exception:
                    pass
                return [self._card_from({"url": page.url, "nombre": name, "texto": ""})]
            self.log(f"Sin resultados para «{query}»", "warn")
            return []

        previous = -1
        unchanged = 0
        while unchanged < 6:
            self._check()
            count = await page.locator('div[role=feed] a[href*="/maps/place/"]').count()
            self.on_event("scroll", loaded=count)

            if max_results and count >= max_results:
                break
            if await page.get_by_text(END_OF_LIST_TEXTS[0]).count() or \
               await page.get_by_text(END_OF_LIST_TEXTS[1]).count():
                break

            await feed.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            await page.wait_for_timeout(1600)

            if count == previous:
                unchanged += 1
            else:
                unchanged = 0
                previous = count

        raw_cards = await page.evaluate(CARDS_JS)
        cards, seen = [], set()
        for raw in raw_cards:
            card = self._card_from(raw)
            key = card["place_id"] or card["url"].split("?")[0]
            if key in seen:
                continue
            seen.add(key)
            cards.append(card)
        return cards[:max_results] if max_results else cards

    def _card_from(self, raw):
        place_id, cid, lat, lng = place_ids_from_url(raw["url"])
        card = {
            "url": raw["url"],
            "nombre_lista": raw.get("nombre", ""),
            "place_id": place_id,
            "cid": cid,
            "lat": lat,
            "lng": lng,
        }
        card.update({f"lista_{k}": v for k, v in parse_card(raw).items()})
        return card

    async def _accept_consent(self, page):
        if "consent." not in page.url:
            return
        for label in ("Aceptar todo", "Accept all", "Rechazar todo", "Reject all"):
            button = page.get_by_role("button", name=label)
            if await button.count():
                await button.first.click()
                await page.wait_for_load_state("domcontentloaded")
                return

    # ----------------------------------------------------------- detail phase

    async def _scrape_details(self, context, cards):
        queue = asyncio.Queue()
        for position, card in enumerate(cards, start=1):
            queue.put_nowait((position, card))

        results = [None] * len(cards)
        done = 0

        async def worker():
            nonlocal done
            page = await context.new_page()
            # No descargar imágenes ni fuentes: acelera mucho la carga.
            await page.route(
                re.compile(r".*\.(png|jpe?g|gif|webp|woff2?|ttf)(\?.*)?$"),
                lambda route: route.abort(),
            )
            try:
                while not queue.empty():
                    self._check()
                    position, card = queue.get_nowait()
                    # Pausa aleatoria para no martillar a Google con un ritmo fijo.
                    await page.wait_for_timeout(random.randint(400, 1400))
                    business = await self._scrape_one(page, card)
                    results[position - 1] = business
                    done += 1
                    self.on_event("business", business=business, done=done, total=len(cards))
            finally:
                await page.close()

        await asyncio.gather(*(worker() for _ in range(min(self.concurrency, len(cards)))))
        return [r for r in results if r]

    async def _scrape_one(self, page, card):
        url = card["url"]
        if "hl=" not in url:
            url += ("&" if "?" in url else "?") + "hl=es"

        detail = None
        for attempt in range(2):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.locator("div[role=main] h1").first.wait_for(timeout=10000)
                # Esperar a que cargue el bloque de información (dirección, teléfono...).
                try:
                    await page.locator("div[role=main] [data-item-id]").first.wait_for(timeout=4000)
                except Exception:
                    pass
                await page.wait_for_timeout(600)
                detail = parse_detail(await page.evaluate(DETAIL_JS))
                if detail["nombre"]:
                    break
            except Cancelled:
                raise
            except Exception as error:
                if attempt == 1:
                    self.log(f"No se pudo leer «{card['nombre_lista']}»: {str(error)[:80]}", "warn")
                await page.wait_for_timeout(1500)

        if not detail or not detail["nombre"]:
            detail = parse_detail({"nombre": card["nombre_lista"]})
            detail["estado_negocio"] = card["lista_cerrado"] or ""
            detail["perfil_reclamado"] = ""

        _, _, lat, lng = place_ids_from_url(page.url)

        business = dict(detail)
        business["nombre"] = detail["nombre"] or card["nombre_lista"]
        business["categoria"] = detail["categoria"] or card["lista_categoria"]
        business["rating"] = detail["rating"] if detail["rating"] is not None else card["lista_rating"]
        business["resenas"] = detail["resenas"] if detail["resenas"] is not None else card["lista_resenas"]
        if card["lista_cerrado"] and not business["estado_negocio"].startswith("Cerrado"):
            business["estado_negocio"] = card["lista_cerrado"]
        business["lat"] = card["lat"] if card["lat"] is not None else lat
        business["lng"] = card["lng"] if card["lng"] is not None else lng
        business["place_id"] = card["place_id"]
        business["busqueda"] = card.get("busqueda", "")
        business["distancia_km"] = card.get("distancia_km")
        if card["place_id"]:
            business["google_maps"] = (
                "https://www.google.com/maps/search/?api=1&query="
                f"{quote(business['nombre'])}&query_place_id={card['place_id']}"
            )
        else:
            business["google_maps"] = card["url"].split("?")[0]
        return business
