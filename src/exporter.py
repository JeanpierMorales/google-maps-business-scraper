import os
import re
import pandas as pd
from datetime import datetime


COLUMNS = [
    "nombre",
    "categoria",
    "direccion",
    "telefono",
    "sitio_web",
    "instagram",
    "facebook",
    "tiktok",
    "rating"
]


def clean_filename(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9áéíóúñ]+",
        "_",
        text
    )

    return text.strip("_")


def export_to_excel(
    businesses,
    business_type,
    location
):

    os.makedirs(
        "output",
        exist_ok=True
    )

    df = pd.DataFrame(
        businesses
    )

    for column in COLUMNS:

        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS]

    # Eliminar duplicados
    df = df.drop_duplicates(
        subset=[
            "nombre",
            "direccion"
        ]
    )

    date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    business_name = clean_filename(
        business_type
    )

    location_name = clean_filename(
        location
    )

    filename = (
        f"{business_name}_"
        f"{location_name}_"
        f"{date}.xlsx"
    )

    path = os.path.join(
        "output",
        filename
    )

    df.to_excel(
        path,
        index=False,
        engine="openpyxl"
    )

    return path