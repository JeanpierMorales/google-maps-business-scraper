from src.scraper import GoogleMapsScraper
from src.social_scraper import get_social_links
from src.exporter import export_to_excel


def main():
    print("\n=== Google Maps Business Scraper ===\n")

    location = input("Ubicación: ").strip()
    business_type = input("Tipo de negocio: ").strip()

    if not location or not business_type:
        print("La ubicación y el tipo de negocio son obligatorios.")
        return

    search_query = f"{business_type} en {location}"

    print(f"\nBuscando: {search_query}\n")

    scraper = GoogleMapsScraper(headless=False)

    businesses = scraper.search(search_query)

    if not businesses:
        print("No se encontraron negocios.")
        return

    print(f"\nNegocios encontrados: {len(businesses)}")
    print("Buscando redes sociales...\n")

    for index, business in enumerate(businesses, start=1):

        website = business.get("sitio_web")

        print(
            f"[{index}/{len(businesses)}] "
            f"{business.get('nombre', 'Sin nombre')}"
        )

        if website:
            socials = get_social_links(website)

            business["instagram"] = socials["instagram"]
            business["facebook"] = socials["facebook"]
            business["tiktok"] = socials["tiktok"]

        else:
            business["instagram"] = ""
            business["facebook"] = ""
            business["tiktok"] = ""

    file_path = export_to_excel(
        businesses,
        business_type,
        location
    )

    print("\n==============================")
    print("Proceso terminado")
    print(f"Negocios: {len(businesses)}")
    print(f"Archivo: {file_path}")
    print("==============================\n")


if __name__ == "__main__":
    main()