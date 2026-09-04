# Google Maps Business Scraper

A simple Python scraper that collects business information from Google Maps and exports the results to Excel.

The scraper searches businesses by:

* Location
* Business category

It then processes the available Google Maps results and extracts useful contact and business information.

## Features

* Search businesses by location
* Search businesses by category
* Automatically scroll through Google Maps results
* Extract multiple businesses from the search area
* Remove duplicate results
* Export results to Excel
* Detect social media links from business websites

## Extracted Data

The generated Excel file contains the following columns:

| Column      | Description          |
| ----------- | -------------------- |
| `nombre`    | Business name        |
| `categoria` | Business category    |
| `direccion` | Business address     |
| `telefono`  | Contact phone number |
| `sitio_web` | Official website     |
| `instagram` | Instagram profile    |
| `facebook`  | Facebook page        |
| `tiktok`    | TikTok profile       |
| `rating`    | Google Maps rating   |

Each row represents one business found in the selected location.

## Project Structure

```text
google-maps-business-scraper/
│
├── main.py
│
├── src/
│   ├── scraper.py
│   ├── social_scraper.py
│   └── exporter.py
│
├── output/
├── requirements.txt
├── .gitignore
└── README.md
```

## Technologies

* Python
* Playwright
* Pandas
* OpenPyXL
* BeautifulSoup4
* Requests

## Installation

Clone the repository:

```bash
git clone https://github.com/JeanpierMorales/google-maps-business-scraper.git
cd google-maps-business-scraper
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
playwright install chromium
```

## Usage

Run:

```bash
python main.py
```

The program will ask for:

```text
Ubicación: La Arena, Piura
Tipo de negocio: Barberías
```

The scraper will generate a Google Maps search equivalent to:

```text
Barberías en La Arena, Piura
```

It will then:

1. Open Google Maps.
2. Load the available businesses.
3. Scroll through the results.
4. Collect unique business URLs.
5. Visit each business.
6. Extract its information.
7. Visit the business website when available.
8. Detect Instagram, Facebook and TikTok links.
9. Export the results to Excel.

## Output

Generated files are stored inside:

```text
output/
```

Example:

```text
output/barberias_la_arena_piura_2026-09-04.xlsx
```

Example output:

| nombre           | categoria | direccion       | telefono      | sitio_web   | instagram             | facebook | tiktok | rating |
| ---------------- | --------- | --------------- | ------------- | ----------- | --------------------- | -------- | ------ | ------ |
| Barbería Example | Barbería  | La Arena, Piura | +51 999999999 | example.com | instagram.com/example |          |        | 4.7    |

## Current Scope

This project is intentionally kept simple.

The current goal is:

```text
Location + Business Category
            ↓
       Google Maps
            ↓
    Businesses Found
            ↓
  Business Information
            ↓
          Excel
```

The project does not currently include:

* Web interface
* Database
* Authentication
* Cloud deployment
* Advanced analytics
* Anti-bot bypass systems

These features may be considered later only if they become necessary.

## Limitations

Google Maps is a dynamic application and its HTML structure may change over time.

Because of this, some Playwright selectors may require updates if Google modifies the Maps interface.

Social media profiles are mainly detected by visiting the official website of each business. If a business has no website, or its social profiles are not linked from the website, those fields may remain empty.

Search results are also determined by Google Maps and may not represent every existing business in a geographic area.

## Responsible Use

This repository is intended primarily for educational and development purposes.

Automated extraction of Google Maps content may be subject to Google's terms and policies.

For production, commercial, or high-volume applications, consider using official Google Maps Platform APIs such as the Places API.

This project does not include mechanisms designed to bypass CAPTCHA, access restrictions, anti-bot systems, rate limits, or other security controls.

## Author

Jeanpier Morales

GitHub: [JeanpierMorales](https://github.com/JeanpierMorales)

## License

No license has been defined yet.
