import argparse

from src.pipeline import run_job


def print_event(kind, **data):
    if kind == "phase":
        print(f"\n▶ {data['message']}")
    elif kind == "log":
        print(f"  {data['message']}")
    elif kind == "scroll":
        print(f"  Negocios cargados: {data['loaded']}", end="\r")
    elif kind == "business":
        business = data["business"]
        print(f"  [{data['done']}/{data['total']}] {business.get('nombre', 'Sin nombre')}")
    elif kind == "web":
        print(f"  Webs revisadas: {data['done']}/{data['total']}", end="\r")


def main():
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper")
    parser.add_argument("--tipo", help="Tipo de negocio (varios separados por coma)")
    parser.add_argument("--ubicacion", help="Ciudad o zona, p. ej. «Piura»")
    parser.add_argument("--zonas", default="", help="Zonas extra separadas por coma")
    parser.add_argument("--max", type=int, default=0, help="Máximo por búsqueda (0 = sin límite)")
    parser.add_argument("--ver-navegador", action="store_true", help="Mostrar el navegador")
    parser.add_argument("--sin-webs", action="store_true", help="No revisar sitios web")
    args = parser.parse_args()

    print("\n=== Google Maps Business Scraper ===\n")

    business_type = args.tipo or input("Tipo de negocio: ").strip()
    location = args.ubicacion or input("Ubicación: ").strip()

    if not location or not business_type:
        print("La ubicación y el tipo de negocio son obligatorios.")
        return

    result = run_job(
        {
            "tipo": business_type,
            "ubicacion": location,
            "zonas": args.zonas,
            "max_resultados": args.max,
            "headless": not args.ver_navegador,
            "analizar_webs": not args.sin_webs,
        },
        emit=print_event,
    )

    summary = result["summary"]
    print("\n==============================")
    print("Proceso terminado" + (f" ({result['stats']['interrumpido']})"
                                 if result["stats"]["interrumpido"] else ""))
    print(f"Negocios:        {summary['total']}")
    print(f"Sin web (leads): {summary['sin_web']}")
    print(f"Con WhatsApp:    {summary['con_whatsapp']}")
    print(f"Prioridad alta:  {summary['prioridad_alta']}")
    print(f"Archivo:         {result['excel']}")
    print("==============================\n")


if __name__ == "__main__":
    main()
