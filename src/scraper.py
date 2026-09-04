import time
from playwright.sync_api import sync_playwright


class GoogleMapsScraper:

    def __init__(self, headless=False):
        self.headless = headless

    def search(self, query):

        businesses = []

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=self.headless
            )

            page = browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 900
                }
            )

            page.goto(
                "https://www.google.com/maps",
                wait_until="domcontentloaded"
            )

            page.wait_for_timeout(3000)

            search_box = page.locator(
                'input[name="q"]'
            )

            search_box.fill(query)
            search_box.press("Enter")

            print("Esperando resultados...")

            page.wait_for_timeout(5000)

            feed = page.locator(
                'div[role="feed"]'
            )

            try:
                feed.wait_for(timeout=10000)

            except Exception:
                print(
                    "No se encontró el panel de resultados."
                )

                browser.close()
                return businesses

            self._scroll_results(
                page,
                feed
            )

            links = page.locator(
                'a[href*="/maps/place/"]'
            )

            urls = []

            count = links.count()

            for i in range(count):

                try:
                    href = links.nth(i).get_attribute(
                        "href"
                    )

                    if href and href not in urls:
                        urls.append(href)

                except Exception:
                    continue

            print(
                f"\nResultados únicos detectados: {len(urls)}\n"
            )

            for index, url in enumerate(
                urls,
                start=1
            ):

                print(
                    f"[{index}/{len(urls)}] Analizando negocio..."
                )

                try:

                    page.goto(
                        url,
                        wait_until="domcontentloaded"
                    )

                    page.wait_for_timeout(2500)

                    business = self._extract_business(
                        page
                    )

                    if business["nombre"]:
                        businesses.append(
                            business
                        )

                except Exception as error:

                    print(
                        f"Error leyendo negocio: {error}"
                    )

            browser.close()

        return businesses

    def _scroll_results(
        self,
        page,
        feed
    ):

        print("Cargando negocios...")

        previous_count = 0
        unchanged_rounds = 0

        while unchanged_rounds < 5:

            links = page.locator(
                'a[href*="/maps/place/"]'
            )

            current_count = links.count()

            print(
                f"Negocios cargados: {current_count}",
                end="\r"
            )

            feed.evaluate(
                """
                element => {
                    element.scrollTop =
                    element.scrollHeight
                }
                """
            )

            page.wait_for_timeout(2000)

            if current_count == previous_count:

                unchanged_rounds += 1

            else:

                unchanged_rounds = 0
                previous_count = current_count

        print(
            f"\nCarga finalizada: {previous_count}"
        )

    def _extract_business(
        self,
        page
    ):

        business = {
            "nombre": "",
            "categoria": "",
            "direccion": "",
            "telefono": "",
            "sitio_web": "",
            "instagram": "",
            "facebook": "",
            "tiktok": "",
            "rating": ""
        }

        # Nombre
        try:

            business["nombre"] = (
                page.locator("h1")
                .first
                .inner_text()
                .strip()
            )

        except Exception:
            pass

        # Rating
        try:

            rating_element = page.locator(
                '[role="img"][aria-label*="estrella"], '
                '[role="img"][aria-label*="star"]'
            ).first

            aria_label = rating_element.get_attribute(
                "aria-label"
            )

            if aria_label:
                business["rating"] = (
                    aria_label
                    .split()[0]
                    .replace(",", ".")
                )

        except Exception:
            pass

        # Dirección
        business["direccion"] = (
            self._get_button_value(
                page,
                "address"
            )
        )

        # Teléfono
        business["telefono"] = (
            self._get_button_value(
                page,
                "phone"
            )
        )

        # Website
        try:

            website = page.locator(
                'a[data-item-id="authority"]'
            ).first

            if website.count() > 0:

                business["sitio_web"] = (
                    website.get_attribute(
                        "href"
                    ) or ""
                )

        except Exception:
            pass

        # Categoría
        try:

            category_buttons = page.locator(
                'button[jsaction*="category"]'
            )

            if category_buttons.count():

                business["categoria"] = (
                    category_buttons
                    .first
                    .inner_text()
                    .strip()
                )

        except Exception:
            pass

        return business

    def _get_button_value(
        self,
        page,
        item
    ):

        try:

            element = page.locator(
                f'[data-item-id*="{item}"]'
            ).first

            if element.count() == 0:
                return ""

            aria_label = element.get_attribute(
                "aria-label"
            )

            if aria_label and ":" in aria_label:

                return (
                    aria_label
                    .split(":", 1)[1]
                    .strip()
                )

            return (
                element
                .inner_text()
                .strip()
            )

        except Exception:

            return ""