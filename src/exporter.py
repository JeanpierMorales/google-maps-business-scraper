"""Exportación a Excel con varias hojas, formato, hipervínculos y resumen."""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

# (clave, encabezado, ancho, tipo)
COLUMNS = [
    ("n", "#", 5, "int"),
    ("prioridad", "Prioridad", 11, "text"),
    ("lead_score", "Puntaje", 9, "int"),
    ("motivos", "Por qué es oportunidad", 44, "wrap"),
    ("nombre", "Nombre", 34, "bold"),
    ("categoria", "Categoría", 24, "text"),
    ("rating", "Rating", 8, "rating"),
    ("resenas", "Reseñas", 9, "int"),
    ("direccion", "Dirección", 42, "wrap"),
    ("plus_code", "Plus Code", 20, "text"),
    ("telefono", "Teléfono", 16, "text"),
    ("telefono_intl", "Teléfono (internacional)", 19, "text"),
    ("tipo_telefono", "Tipo tel.", 9, "text"),
    ("whatsapp", "WhatsApp", 30, "link"),
    ("email", "Email", 30, "email"),
    ("sitio_web", "Sitio web", 36, "link"),
    ("tipo_web", "Tipo de web", 20, "text"),
    ("estado_web", "Estado web", 17, "text"),
    ("plataforma_web", "Plataforma web", 14, "text"),
    ("web_responsive", "Web móvil", 10, "text"),
    ("instagram", "Instagram", 36, "link"),
    ("facebook", "Facebook", 36, "link"),
    ("tiktok", "TikTok", 30, "link"),
    ("youtube", "YouTube", 30, "link"),
    ("linkedin", "LinkedIn", 30, "link"),
    ("twitter", "X / Twitter", 26, "link"),
    ("horario", "Horario", 40, "wrap"),
    ("estado_negocio", "Estado del negocio", 20, "text"),
    ("perfil_reclamado", "Perfil reclamado", 11, "text"),
    ("distancia_km", "Distancia al centro (km)", 12, "text"),
    ("lat", "Latitud", 11, "coord"),
    ("lng", "Longitud", 11, "coord"),
    ("google_maps", "Google Maps", 18, "maps"),
    ("place_id", "Place ID", 30, "text"),
    ("busqueda", "Búsqueda", 30, "text"),
]

LEAD_COLUMNS = [
    "n", "prioridad", "lead_score", "motivos", "nombre", "categoria", "rating", "resenas",
    "telefono", "whatsapp", "email", "tipo_web", "sitio_web", "instagram", "facebook",
    "tiktok", "perfil_reclamado", "direccion", "google_maps",
]

NO_WEB_TYPES = ("Sin web", "Solo redes sociales", "Linktree / bio", "Directorio / plataforma")

INK = "1F2A37"
ACCENT = "0F766E"
MUTED = "6B7280"
PRIORITY_FILLS = {
    "Alta": ("DCFCE7", "166534"),
    "Media": ("FEF3C7", "92400E"),
    "Baja": ("F3F4F6", "4B5563"),
    "Descartar": ("FEE2E2", "991B1B"),
}

HEADER_FILL = PatternFill("solid", fgColor=INK)
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
LINK_FONT = Font(color="0563C1", underline="single")
THIN = Side(style="thin", color="E5E7EB")


def clean_filename(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúñü]+", "_", text)
    return text.strip("_")[:60]


def build_filename(business_type, location, stamp=None):
    stamp = stamp or datetime.now().strftime("%Y-%m-%d_%H%M")
    return f"{clean_filename(business_type)}_{clean_filename(location)}_{stamp}"


def _link_label(key, value):
    if key == "google_maps":
        return "Abrir en Maps"
    if key == "whatsapp":
        return value.replace("https://", "")
    return re.sub(r"^https?://(www\.)?", "", value).rstrip("/")


def _write_table(ws, businesses, keys, table_name, start_row=1):
    specs = {c[0]: c for c in COLUMNS}
    columns = [specs[k] for k in keys]

    for col, (_, header, width, _) in enumerate(columns, start=1):
        cell = ws.cell(row=start_row, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[start_row].height = 30

    for r, business in enumerate(businesses, start=start_row + 1):
        for col, (key, _, _, kind) in enumerate(columns, start=1):
            value = business.get(key, "")
            if value is None:
                value = ""
            cell = ws.cell(row=r, column=col)

            if kind in ("link", "maps") and value:
                cell.value = _link_label(key, value)
                cell.hyperlink = value
                cell.font = LINK_FONT
            elif kind == "email" and value:
                cell.value = value
                cell.hyperlink = f"mailto:{value}"
                cell.font = LINK_FONT
            else:
                cell.value = value

            if kind == "bold":
                cell.font = Font(bold=True, color=INK)
            elif kind == "wrap":
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            elif kind == "rating" and value != "":
                cell.number_format = "0.0"
            elif kind == "coord" and value != "":
                cell.number_format = "0.000000"

            if key == "prioridad" and value in PRIORITY_FILLS:
                bg, fg = PRIORITY_FILLS[value]
                cell.fill = PatternFill("solid", fgColor=bg)
                cell.font = Font(bold=True, color=fg)
                cell.alignment = Alignment(horizontal="center")

            if not cell.alignment.vertical:
                cell.alignment = Alignment(vertical="top", wrap_text=cell.alignment.wrap_text)

    last_row = start_row + max(len(businesses), 1)
    last_col = get_column_letter(len(columns))
    ref = f"A{start_row}:{last_col}{last_row}"

    if businesses:
        table = Table(displayName=table_name, ref=ref)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleLight1", showRowStripes=True, showColumnStripes=False
        )
        ws.add_table(table)

        if "rating" in keys:
            letter = get_column_letter(keys.index("rating") + 1)
            ws.conditional_formatting.add(
                f"{letter}{start_row + 1}:{letter}{last_row}",
                ColorScaleRule(start_type="num", start_value=1, start_color="F8696B",
                               mid_type="num", mid_value=3.8, mid_color="FFEB84",
                               end_type="num", end_value=5, end_color="63BE7B"),
            )
        if "lead_score" in keys:
            letter = get_column_letter(keys.index("lead_score") + 1)
            ws.conditional_formatting.add(
                f"{letter}{start_row + 1}:{letter}{last_row}",
                ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                               end_type="num", end_value=100, end_color="63BE7B"),
            )

    # Congelar encabezado y la columna del nombre.
    name_col = keys.index("nombre") + 2 if "nombre" in keys else 1
    ws.freeze_panes = ws.cell(row=start_row + 1, column=name_col)
    ws.sheet_view.zoomScale = 110


def _pct(part, total):
    return part / total if total else 0


def build_summary(businesses, params, stats):
    total = len(businesses)
    ratings = [b["rating"] for b in businesses if isinstance(b.get("rating"), (int, float))]
    reviews = [b["resenas"] for b in businesses if isinstance(b.get("resenas"), int)]

    def count(fn):
        return sum(1 for b in businesses if fn(b))

    return {
        "total": total,
        "con_telefono": count(lambda b: b.get("telefono")),
        "con_whatsapp": count(lambda b: b.get("whatsapp")),
        "con_email": count(lambda b: b.get("email")),
        "con_web_propia": count(lambda b: b.get("tipo_web") == "Web propia"),
        "sin_web": count(lambda b: b.get("tipo_web") in NO_WEB_TYPES),
        "web_con_problemas": count(lambda b: b.get("tipo_web") == "Web propia"
                                   and b.get("estado_web") not in ("OK", "OK (sin HTTPS)", "")),
        "con_instagram": count(lambda b: b.get("instagram")),
        "con_facebook": count(lambda b: b.get("facebook")),
        "con_tiktok": count(lambda b: b.get("tiktok")),
        "no_reclamados": count(lambda b: b.get("perfil_reclamado") == "No"),
        "prioridad_alta": count(lambda b: b.get("prioridad") == "Alta"),
        "prioridad_media": count(lambda b: b.get("prioridad") == "Media"),
        "prioridad_baja": count(lambda b: b.get("prioridad") == "Baja"),
        "rating_promedio": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "resenas_total": sum(reviews),
        "descartados": stats.get("descartados", 0),
    }


def _write_summary(ws, businesses, params, stats, summary):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 4
    ws.column_dimensions["F"].width = 30
    ws.column_dimensions["G"].width = 11
    ws.column_dimensions["H"].width = 11
    ws.column_dimensions["I"].width = 11

    ws["B2"] = "Reporte de negocios — Google Maps"
    ws["B2"].font = Font(bold=True, size=18, color=INK)
    ws["B3"] = f"{params.get('tipo', '')} en {params.get('ubicacion', '')}"
    ws["B3"].font = Font(size=12, color=ACCENT, bold=True)

    info = [
        ("Fecha", stats.get("fecha", "")),
        ("Duración", stats.get("duracion", "")),
        ("Búsquedas realizadas", len(params.get("queries", []))),
        ("Consultas", " | ".join(params.get("queries", []))),
        ("Filtros", params.get("filtros_texto", "Ninguno")),
    ]
    row = 5
    for label, value in info:
        ws.cell(row=row, column=2, value=label).font = Font(color=MUTED)
        cell = ws.cell(row=row, column=3, value=value)
        cell.alignment = Alignment(wrap_text=False)
        row += 1

    row += 1
    ws.cell(row=row, column=2, value="Indicador").font = HEADER_FONT
    ws.cell(row=row, column=3, value="Cantidad").font = HEADER_FONT
    ws.cell(row=row, column=4, value="%").font = HEADER_FONT
    for col in (2, 3, 4):
        ws.cell(row=row, column=col).fill = HEADER_FILL
    row += 1

    total = summary["total"]
    kpis = [
        ("Negocios encontrados", total, None),
        ("Con teléfono", summary["con_telefono"], True),
        ("Con WhatsApp (móvil)", summary["con_whatsapp"], True),
        ("Con email", summary["con_email"], True),
        ("Con web propia", summary["con_web_propia"], True),
        ("Sin web propia (leads)", summary["sin_web"], True),
        ("Web propia con problemas", summary["web_con_problemas"], True),
        ("Con Instagram", summary["con_instagram"], True),
        ("Con Facebook", summary["con_facebook"], True),
        ("Con TikTok", summary["con_tiktok"], True),
        ("Perfil de Google no reclamado", summary["no_reclamados"], True),
        ("Prioridad alta", summary["prioridad_alta"], True),
        ("Prioridad media", summary["prioridad_media"], True),
        ("Prioridad baja", summary["prioridad_baja"], True),
        ("Rating promedio", summary["rating_promedio"], None),
        ("Reseñas totales", summary["resenas_total"], None),
        ("Descartados por filtros / cerrados", summary["descartados"], None),
    ]
    for label, value, pct in kpis:
        ws.cell(row=row, column=2, value=label)
        ws.cell(row=row, column=3, value=value if value is not None else "—")
        if pct:
            cell = ws.cell(row=row, column=4, value=_pct(value, total))
            cell.number_format = "0%"
        for col in (2, 3, 4):
            ws.cell(row=row, column=col).border = Border(bottom=THIN)
        row += 1

    # Desglose por categoría.
    cat_row = 5
    headers = ["Categoría", "Negocios", "Rating prom.", "Sin web"]
    for i, header in enumerate(headers):
        cell = ws.cell(row=cat_row, column=6 + i, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    groups = defaultdict(list)
    for b in businesses:
        groups[b.get("categoria") or "Sin categoría"].append(b)
    for name, items in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:30]:
        cat_row += 1
        ratings = [b["rating"] for b in items if isinstance(b.get("rating"), (int, float))]
        ws.cell(row=cat_row, column=6, value=name)
        ws.cell(row=cat_row, column=7, value=len(items))
        cell = ws.cell(row=cat_row, column=8, value=round(sum(ratings) / len(ratings), 2) if ratings else "—")
        cell.number_format = "0.0"
        ws.cell(row=cat_row, column=9, value=sum(1 for b in items if b.get("tipo_web") in NO_WEB_TYPES))
        for col in range(6, 10):
            ws.cell(row=cat_row, column=col).border = Border(bottom=THIN)

    row += 1
    notes = [
        "Cómo leer este reporte:",
        "• «Negocios»: todos los resultados, ordenados por puntaje de oportunidad.",
        "• «Leads sin web»: sin sitio web o que solo usan redes/directorios — los mejores prospectos para vender una web.",
        "• «Webs a mejorar»: tienen web pero está caída, sin HTTPS o no se adapta al móvil.",
        "• Puntaje 0–100: sin web (+35), WhatsApp (+20), perfil no reclamado (+15), muchas reseñas (+15), rating ≥ 4 (+10).",
        "• Google Maps limita cada búsqueda a ~120 resultados: usa «zonas» en la app para cubrir más.",
    ]
    for line in notes:
        cell = ws.cell(row=row, column=2, value=line)
        cell.font = Font(color=MUTED, bold=line.endswith(":"))
        row += 1


def export_to_excel(businesses, business_type, location, params=None, stats=None,
                    discarded=None, basename=None):
    """Genera el .xlsx (y un .json con los mismos datos para la app web)."""

    params = params or {"tipo": business_type, "ubicacion": location, "queries": []}
    stats = stats or {}
    discarded = discarded or []
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    basename = basename or build_filename(business_type, location)
    path = os.path.join(OUTPUT_DIR, f"{basename}.xlsx")

    all_keys = [c[0] for c in COLUMNS]
    summary = build_summary(businesses, params, stats)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"
    _write_summary(ws, businesses, params, stats, summary)

    ws = wb.create_sheet("Negocios")
    _write_table(ws, businesses, all_keys, "Negocios")

    leads = [b for b in businesses if b.get("tipo_web") in NO_WEB_TYPES
             and not b.get("estado_negocio", "").startswith("Cerrado")]
    ws = wb.create_sheet("Leads sin web")
    _write_table(ws, leads, LEAD_COLUMNS, "LeadsSinWeb")

    to_improve = [b for b in businesses if b.get("tipo_web") == "Web propia" and (
        b.get("estado_web") not in ("OK", "") or b.get("web_responsive") == "No")]
    ws = wb.create_sheet("Webs a mejorar")
    _write_table(ws, to_improve, LEAD_COLUMNS[:12] + ["estado_web", "plataforma_web",
                                                     "web_responsive", "sitio_web", "google_maps"],
                 "WebsAMejorar")

    with_web = [b for b in businesses if b.get("tipo_web") == "Web propia"]
    ws = wb.create_sheet("Con web")
    _write_table(ws, with_web, all_keys, "ConWeb")

    if discarded:
        ws = wb.create_sheet("Descartados")
        _write_table(ws, discarded, all_keys, "Descartados")

    wb.properties.title = f"{business_type} en {location}"
    wb.properties.creator = "Google Maps Business Scraper"
    wb.save(path)

    with open(os.path.join(OUTPUT_DIR, f"{basename}.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "params": params,
            "stats": stats,
            "summary": summary,
            "businesses": businesses,
            "discarded": discarded,
            "excel": os.path.basename(path),
        }, fh, ensure_ascii=False, indent=1, default=str)

    return path, summary


def category_counts(businesses):
    return Counter(b.get("categoria") or "Sin categoría" for b in businesses).most_common()
