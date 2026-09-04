import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


SOCIAL_DOMAINS = {
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "tiktok": "tiktok.com"
}


def get_social_links(website):

    socials = {
        "instagram": "",
        "facebook": "",
        "tiktok": ""
    }

    if not website:
        return socials

    try:

        response = requests.get(
            website,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = soup.find_all(
            "a",
            href=True
        )

        for link in links:

            href = urljoin(
                website,
                link["href"]
            )

            href_lower = href.lower()

            for social, domain in SOCIAL_DOMAINS.items():

                if (
                    domain in href_lower
                    and not socials[social]
                ):

                    socials[social] = href

        return socials

    except Exception:

        return socials