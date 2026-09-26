"""Análisis del sitio web de cada negocio: redes sociales, emails, WhatsApp,
estado de la web y plataforma con la que está hecha."""

import re
import warnings
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.normalize import (
    classify_website,
    clean_social_url,
    domain_of,
    is_whatsapp,
    social_network_of,
    whatsapp_number,
)


warnings.filterwarnings("ignore", message="Unverified HTTPS request")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}

SOCIAL_KEYS = ("instagram", "facebook", "tiktok", "youtube", "linkedin", "twitter")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
EMAIL_BLOCKLIST = (
    "example.", "sentry", "wixpress", "domain.com", "email.com", "tuemail",
    "yourmail", "correo.com", "@2x", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".svg", "godaddy", "wordpress.com", "@sentry", "u003e",
)

CONTACT_HINTS = ("contact", "contacto", "contactanos", "contáctanos", "nosotros",
                 "about", "ubicanos", "ubícanos")

PLATFORM_SIGNATURES = (
    ("WordPress", ("wp-content", "wp-includes")),
    ("Wix", ("wixstatic.com", "wix.com", "_wixCssImports")),
    ("Shopify", ("cdn.shopify.com", "shopify.theme")),
    ("Squarespace", ("squarespace.com", "static1.squarespace")),
    ("Webflow", ("webflow.com", "data-wf-page")),
    ("Google Sites", ("sites.google.com", "gstatic.com/sites")),
    ("Blogger", ("blogger.com", "blogspot.com")),
    ("GoDaddy", ("godaddy", "img1.wsimg.com")),
    ("Jimdo", ("jimdo",)),
    ("Weebly", ("weebly",)),
    ("Tiendanube", ("tiendanube", "nuvemshop")),
    ("Next.js", ("__NEXT_DATA__", "/_next/")),
    ("React/Vite", ("/assets/index-", 'id="root"')),
)


def empty_result(website=""):
    result = {key: "" for key in SOCIAL_KEYS}
    result.update({
        "email": "",
        "whatsapp_web": "",
        "tipo_web": classify_website(website),
        "estado_web": "",
        "plataforma_web": "",
        "web_responsive": "",
    })
    return result


def _fetch(url, timeout=12):
    try:
        return requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
    except requests.exceptions.SSLError:
        # Muchas webs pequeñas tienen el certificado vencido: igual se leen.
        return requests.get(url, timeout=timeout, headers=HEADERS,
                            allow_redirects=True, verify=False)


def _collect_from_html(html, base_url, result, emails):
    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if href.lower().startswith("mailto:"):
            address = href[7:].split("?")[0].strip()
            if address:
                emails.append(address)
            continue

        absolute = urljoin(base_url, href)

        if is_whatsapp(absolute) and not result["whatsapp_web"]:
            number = whatsapp_number(absolute)
            if number:
                result["whatsapp_web"] = f"https://wa.me/{number}"
            continue

        network = social_network_of(absolute)
        if network and not result[network]:
            cleaned = clean_social_url(absolute)
            if cleaned:
                result[network] = cleaned

    text = soup.get_text(" ", strip=True)
    emails.extend(EMAIL_RE.findall(text))
    # Emails escondidos en atributos o scripts (muy común en Wix/WordPress).
    emails.extend(EMAIL_RE.findall(html[:400000]))

    return soup


def _pick_email(emails, site_domain):
    valid = []
    for email in emails:
        email = email.strip().strip(".").lower()
        if any(bad in email for bad in EMAIL_BLOCKLIST):
            continue
        if email not in valid:
            valid.append(email)
    if not valid:
        return ""
    # Preferir el email con el dominio del propio sitio.
    for email in valid:
        if site_domain and email.split("@")[-1].endswith(site_domain):
            return email
    return valid[0]


def analyze_website(website):
    """Visita la web del negocio (y su página de contacto) y extrae datos."""

    result = empty_result(website)

    if not website:
        return result

    web_type = result["tipo_web"]

    # Si Google Maps enlaza directo a una red social, esa es su "web".
    network = social_network_of(website)
    if network:
        result[network] = clean_social_url(website) or website
        return result
    if is_whatsapp(website):
        number = whatsapp_number(website)
        result["whatsapp_web"] = f"https://wa.me/{number}" if number else website
        return result

    # Directorios: la página es de un tercero, no se extrae nada de ahí.
    if web_type == "Directorio / plataforma":
        return result

    emails = []
    try:
        response = _fetch(website)
    except requests.exceptions.Timeout:
        result["estado_web"] = "No responde"
        return result
    except requests.exceptions.ConnectionError:
        result["estado_web"] = "Caída / dominio inválido"
        return result
    except Exception:
        result["estado_web"] = "Error de conexión"
        return result

    if response.status_code >= 400:
        result["estado_web"] = f"Error {response.status_code}"
        return result

    result["estado_web"] = "OK"
    html = response.text or ""
    final_url = response.url

    if web_type == "Web propia":
        lower = html[:300000].lower()
        for name, signatures in PLATFORM_SIGNATURES:
            if any(sig.lower() in lower for sig in signatures):
                result["plataforma_web"] = name
                break
        result["web_responsive"] = "Sí" if 'name="viewport"' in lower or "name='viewport'" in lower else "No"
        if final_url.startswith("http://") and not website.startswith("http://"):
            result["estado_web"] = "OK (sin HTTPS)"

    soup = _collect_from_html(html, final_url, result, emails)

    # Página de contacto: segunda fuente de emails y redes.
    missing = not emails or not (result["instagram"] or result["facebook"])
    if web_type == "Web propia" and missing:
        site_domain = domain_of(final_url)
        for link in soup.find_all("a", href=True):
            href = urljoin(final_url, link["href"])
            label = (link.get_text(" ", strip=True) + " " + href).lower()
            if domain_of(href) == site_domain and any(h in label for h in CONTACT_HINTS):
                try:
                    contact = _fetch(href, timeout=8)
                    if contact.status_code < 400:
                        _collect_from_html(contact.text or "", contact.url, result, emails)
                except Exception:
                    pass
                break

    result["email"] = _pick_email(emails, domain_of(final_url))
    return result
