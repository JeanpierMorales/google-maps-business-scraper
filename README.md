# Google Maps Business Scraper

Busca negocios en Google Maps por **tipo** y **ubicación**, revisa la web de cada uno y entrega un **Excel detallado de prospectos**, ordenado por oportunidad (quién no tiene web, quién tiene WhatsApp, quién tiene muchas reseñas, etc.).

Incluye una **interfaz web local** para ver el progreso en vivo, filtrar resultados, verlos en un mapa y descargar el Excel.

## Uso rápido

```bash
.venv/bin/python app.py
```

Abre **http://localhost:5050**, escribe el tipo de negocio y la ubicación y pulsa **Buscar negocios**.

También funciona por consola:

```bash
.venv/bin/python main.py                                  # pregunta tipo y ubicación
.venv/bin/python main.py --tipo "barberías" --ubicacion "Piura"
.venv/bin/python main.py --tipo "dentistas" --ubicacion "Piura" --zonas "Castilla, Veintiséis de Octubre" --max 60
```

| Opción CLI        | Qué hace                                                      |
| ----------------- | ------------------------------------------------------------- |
| `--tipo`          | Tipo de negocio (varios separados por coma)                   |
| `--ubicacion`     | Ciudad o zona                                                 |
| `--zonas`         | Zonas/distritos extra para superar el límite de ~120 de Google |
| `--max`           | Máximo por búsqueda (0 = sin límite, hasta el final de la lista) |
| `--ver-navegador` | Muestra el navegador mientras trabaja                         |
| `--sin-webs`      | No revisa los sitios web (más rápido)                         |

## Qué hace

1. **Ubica la zona** en el mapa y ancla ahí las búsquedas (evita que Google devuelva resultados de otra ciudad).
2. **Carga toda la lista** de Google Maps haciendo scroll hasta el final.
3. **Abre cada ficha** en paralelo (varias pestañas): teléfono, dirección, Plus Code, horario semanal, rating, reseñas, si el perfil está reclamado y si el negocio está cerrado.
4. **Revisa el sitio web**: Instagram, Facebook, TikTok, YouTube, LinkedIn, X, emails, WhatsApp, si la web está caída, si es adaptable a móvil y con qué plataforma está hecha (WordPress, Wix, Shopify…).
5. **Clasifica la web**: web propia, solo redes sociales, Linktree, directorio/plataforma o sin web.
6. **Puntúa cada negocio** (0–100) como prospecto y exporta el Excel.

## El Excel

Se guarda en `output/` (un `.xlsx` y un `.json` con los mismos datos para el historial de la app).

| Hoja               | Contenido                                                                 |
| ------------------ | ------------------------------------------------------------------------- |
| **Resumen**        | Parámetros, fecha, duración, indicadores (% con teléfono, web, WhatsApp, redes…) y desglose por categoría |
| **Negocios**       | Todos los resultados (35 columnas), ordenados por puntaje                 |
| **Leads sin web**  | Sin web propia o solo con redes/directorios: los mejores prospectos        |
| **Webs a mejorar** | Tienen web pero está caída, da error o no es móvil                         |
| **Con web**        | Negocios con web propia                                                   |
| **Descartados**    | Cerrados, fuera de la zona o excluidos por filtros (solo si hay)          |

Todas las hojas tienen encabezado congelado, filtros, anchos ajustados y enlaces clicables (WhatsApp, web, redes, Google Maps, email).

**Columnas:** prioridad, puntaje, motivos, nombre, categoría, rating, reseñas, dirección, Plus Code, teléfono (local e internacional), tipo de teléfono, WhatsApp, email, sitio web, tipo de web, estado de la web, plataforma, web móvil, Instagram, Facebook, TikTok, YouTube, LinkedIn, X, horario, estado del negocio, perfil reclamado, distancia al centro, latitud, longitud, enlace de Google Maps, Place ID y búsqueda de origen.

### Puntaje de oportunidad

| Señal                                   | Puntos |
| --------------------------------------- | ------ |
| Sin web (o solo redes / directorio)     | +25 a +35 |
| Web propia caída o con errores          | +30    |
| Web no adaptada a móvil / sin HTTPS     | +10 / +5 |
| Perfil de Google no reclamado           | +15    |
| Móvil con WhatsApp (o solo fijo)        | +20 (+10) |
| Email                                   | +5     |
| 50+ reseñas (o 10+)                     | +15 (+8) |
| Rating ≥ 4.0                            | +10    |
| Sin ningún dato de contacto             | −20    |

**Alta** ≥ 60 · **Media** 35–59 · **Baja** < 35. La lógica está en `src/normalize.py` (`score_business`).

## Filtros (en la app)

Rating mínimo, reseñas mínimas, distancia máxima al centro, solo con teléfono, solo sin web propia, excluir cerrados, revisar webs sí/no, mostrar navegador y número de pestañas en paralelo.

## Estructura

```text
app.py                  Interfaz web (Flask, puerto 5050)
main.py                 CLI
src/pipeline.py         Orquesta todo el proceso (lo usan app.py y main.py)
src/scraper.py          Google Maps con Playwright (async, varias pestañas)
src/social_scraper.py   Análisis del sitio web de cada negocio
src/normalize.py        Teléfonos, URLs, clasificación de web y puntaje
src/exporter.py         Excel con varias hojas + JSON
web/                    HTML, CSS y JS de la interfaz
output/                 Resultados (ignorado por git)
```

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Límites

* Google Maps muestra como máximo ~120 resultados por búsqueda. Usa **zonas** para cubrir más.
* Sin iniciar sesión, Google Maps muestra una "vista limitada": no incluye nivel de precios ni todas las reseñas.
* Si Google cambia el HTML de Maps, algunos selectores de `src/scraper.py` pueden necesitar ajustes.
* Las redes y emails se sacan de la web del negocio: si no tiene web o no las enlaza, quedan vacíos.

## Uso responsable

Proyecto con fines educativos y de desarrollo. La extracción automatizada de Google Maps puede estar sujeta a los términos de Google; para uso comercial o de alto volumen, considera la API oficial de Places. El proyecto no incluye mecanismos para saltar CAPTCHAs ni otros controles de seguridad.

## Autor

Jeanpier Morales · [GitHub](https://github.com/JeanpierMorales)
