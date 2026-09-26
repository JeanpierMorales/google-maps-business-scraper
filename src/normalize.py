"""Limpieza y normalización de datos: teléfonos, URLs y puntaje de oportunidad."""

import re
from urllib.parse import urlparse, parse_qs, urlunparse


# ---------------------------------------------------------------------------
# Teléfonos
# ---------------------------------------------------------------------------

def normalize_phone(raw, country_code="51"):
    """Devuelve (internacional, tipo, whatsapp_url) a partir de un teléfono crudo.

    Las reglas de móvil/fijo solo se aplican a Perú (+51); para otros países
    se devuelve el número en formato internacional sin clasificar.
    """

    if not raw:
        return "", "", ""

    raw = str(raw).strip()
    digits = re.sub(r"\D", "", raw)

    if not digits:
        return "", "", ""

    if raw.startswith("+"):
        full = digits
    elif digits.startswith("00"):
        full = digits[2:]
    elif country_code and digits.startswith(country_code) and len(digits) > 9:
        full = digits
    else:
        full = f"{country_code}{digits.lstrip('0')}"

    local = full[len(country_code):] if full.startswith(country_code) else ""
    kind = ""
    whatsapp = ""

    if country_code == "51" and local:
        if len(local) == 9 and local.startswith("9"):
            kind = "Móvil"
            pretty = f"+51 {local[:3]} {local[3:6]} {local[6:]}"
            whatsapp = f"https://wa.me/51{local}"
        else:
            kind = "Fijo"
            # Lima usa código de área 1, provincias 2 dígitos (73 = Piura).
            area_len = 1 if local.startswith("1") else 2
            pretty = f"+51 {local[:area_len]} {local[area_len:]}"
    else:
        pretty = f"+{full}"

    return pretty, kind, whatsapp


# ---------------------------------------------------------------------------
# URLs y redes sociales
# ---------------------------------------------------------------------------

SOCIAL_DOMAINS = {
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.com", "fb.me"),
    "tiktok": ("tiktok.com",),
    "youtube": ("youtube.com", "youtu.be"),
    "linkedin": ("linkedin.com",),
    "twitter": ("twitter.com", "x.com"),
}

WHATSAPP_DOMAINS = ("wa.me", "whatsapp.com", "wa.link")

BIO_LINK_DOMAINS = (
    "linktr.ee", "beacons.ai", "taplink.cc", "bio.link", "linkin.bio",
    "lnk.bio", "campsite.bio", "solo.to", "hoo.be",
)

# Directorios o plataformas de terceros: la página NO es del negocio,
# así que no se toman redes ni emails de ahí.
DIRECTORY_DOMAINS = (
    "paginasamarillas", "tripadvisor", "rappi", "pedidosya", "ubereats",
    "didi-food", "didifood", "booksy", "fresha", "treatwell", "yelp",
    "foursquare", "doctoralia", "google.com", "goo.gl", "g.page",
    "cylex", "infoisinfo", "guiaempresas", "universidadperu", "restaurantguru",
    "sluurpy", "misterwhat", "tuugo", "hotfrog", "waze.com", "maps.app",
    "booking.com", "airbnb", "expedia", "despegar", "trivago", "agoda",
    "mercadolibre", "olx", "canva.site", "menu.", "cartadigital", "wixsite.com/menu",
    "weibook", "agendapro", "calendly", "setmore", "simplybook", "reservio", "vagaro",
    "squareup.com/appointments", "wa.link", "linkr.bio", "mipagina", "ueniweb", "negocio.site",
    "forms.gle", "docs.google.com/forms", "bit.ly", "linktr.ee/s/",
)

SHARE_PATTERNS = (
    "sharer", "/share", "intent/", "/dialog/", "plugins/", "/hashtag/",
    "/explore/", "/p/", "/reel/", "/watch", "/video/", "/posts/", "/photos/",
    "/events/", "/groups/", "privacy", "/legal", "/help", "/policies",
)


def domain_of(url):
    try:
        host = urlparse(url if "://" in url else f"http://{url}").netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _matches(domain, candidates):
    return any(domain == c or domain.endswith("." + c) or c in domain for c in candidates)


def social_network_of(url):
    domain = domain_of(url)
    for network, domains in SOCIAL_DOMAINS.items():
        if any(domain == d or domain.endswith("." + d) for d in domains):
            return network
    return ""


def is_whatsapp(url):
    return _matches(domain_of(url), WHATSAPP_DOMAINS)


def classify_website(url):
    """Clasifica el enlace "Sitio web" que publica Google Maps."""

    if not url:
        return "Sin web"
    domain = domain_of(url)
    if social_network_of(url) or is_whatsapp(url):
        return "Solo redes sociales"
    if _matches(domain, BIO_LINK_DOMAINS):
        return "Linktree / bio"
    if any(d in url.lower() for d in DIRECTORY_DOMAINS):
        return "Directorio / plataforma"
    return "Web propia"


def clean_social_url(url):
    """Deja solo el perfil: sin parámetros de rastreo ni rutas de posts.

    Devuelve "" si el enlace es un botón de compartir o un post suelto.
    """

    network = social_network_of(url)
    if not network:
        return ""

    parsed = urlparse(url if "://" in url else f"https://{url}")
    path = parsed.path or "/"
    lower = url.lower()

    if network == "facebook" and "profile.php" in path:
        profile_id = parse_qs(parsed.query).get("id", [""])[0]
        if not profile_id:
            return ""
        return f"https://www.facebook.com/profile.php?id={profile_id}"

    if any(p in lower for p in SHARE_PATTERNS):
        # Un post de Facebook/Instagram sigue indicando la cuenta dueña.
        if network in ("facebook", "instagram", "tiktok"):
            first = [s for s in path.split("/") if s]
            if first and first[0] not in ("sharer", "sharer.php", "share", "dialog", "plugins",
                                          "p", "reel", "explore", "hashtag", "watch"):
                return _canonical(network, first[0])
        return ""

    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""

    if network == "youtube":
        handle = "/".join(segments[:2]) if segments[0] in ("c", "channel", "user") else segments[0]
        return f"https://www.youtube.com/{handle}"
    if network == "linkedin":
        return f"https://www.linkedin.com/{'/'.join(segments[:2])}"

    return _canonical(network, segments[0])


def _canonical(network, handle):
    handle = handle.strip()
    if network == "instagram":
        return f"https://www.instagram.com/{handle}/"
    if network == "facebook":
        return f"https://www.facebook.com/{handle}"
    if network == "tiktok":
        if not handle.startswith("@"):
            return ""
        return f"https://www.tiktok.com/{handle}"
    if network == "twitter":
        return f"https://x.com/{handle}"
    return ""


def clean_website(url):
    """Quita parámetros de rastreo (utm, fbclid...) de un sitio web."""

    if not url:
        return ""
    parsed = urlparse(url)
    query = "&".join(
        part for part in parsed.query.split("&")
        if part and not re.match(r"(utm_|fbclid|gclid|y_source|rclk)", part)
    )
    return urlunparse(parsed._replace(query=query, fragment=""))


def whatsapp_number(url):
    """Extrae el número de un enlace wa.me / api.whatsapp.com."""

    parsed = urlparse(url)
    number = parse_qs(parsed.query).get("phone", [""])[0]
    if not number:
        number = parsed.path.strip("/").split("/")[0]
    digits = re.sub(r"\D", "", number)
    return digits if len(digits) >= 8 else ""


# ---------------------------------------------------------------------------
# Puntaje de oportunidad (orientado a vender servicios web / marketing)
# ---------------------------------------------------------------------------

def score_business(b):
    """Calcula puntaje 0-100, prioridad y motivos legibles."""

    if b.get("estado_negocio", "").startswith("Cerrado"):
        return 0, "Descartar", "Negocio cerrado"

    score = 0
    reasons = []

    web_type = b.get("tipo_web", "")
    if web_type == "Sin web":
        score += 35
        reasons.append("Sin sitio web")
    elif web_type == "Solo redes sociales":
        score += 30
        reasons.append("Usa redes como web")
    elif web_type == "Directorio / plataforma":
        score += 30
        reasons.append("Solo aparece en directorios")
    elif web_type == "Linktree / bio":
        score += 25
        reasons.append("Solo tiene Linktree")
    else:
        status = b.get("estado_web", "")
        if status and status != "OK":
            score += 30
            reasons.append(f"Web con problemas ({status})")
        else:
            if b.get("web_responsive") == "No":
                score += 10
                reasons.append("Web no adaptada a móvil")
            if b.get("sitio_web", "").startswith("http://"):
                score += 5
                reasons.append("Web sin HTTPS")

    if b.get("perfil_reclamado") == "No":
        score += 15
        reasons.append("Perfil de Google no reclamado")

    if b.get("whatsapp"):
        score += 20
        reasons.append("Contactable por WhatsApp")
    elif b.get("telefono"):
        score += 10
        reasons.append("Tiene teléfono")

    if b.get("email"):
        score += 5

    reviews = b.get("resenas") or 0
    if reviews >= 50:
        score += 15
        reasons.append(f"Negocio establecido ({reviews} reseñas)")
    elif reviews >= 10:
        score += 8

    rating = b.get("rating") or 0
    if rating >= 4.0:
        score += 10

    if not b.get("telefono") and not b.get("whatsapp") and not b.get("email"):
        score -= 20
        reasons.append("Sin datos de contacto")

    score = max(0, min(100, score))

    if score >= 60:
        priority = "Alta"
    elif score >= 35:
        priority = "Media"
    else:
        priority = "Baja"

    return score, priority, " · ".join(reasons)
