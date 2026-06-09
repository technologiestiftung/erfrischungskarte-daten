import csv
import json
import re
from pathlib import Path

# ==== Dateien (bei Bedarf anpassen) ====
INPUT_CSV = "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Badestellen-Strandbad/badestellen-strandbad-roh.csv"

OUTPUT_BADESTELLEN_CSV = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/badestellen_formatiert.csv"
OUTPUT_BADESTELLEN_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/badestellen_formatiert.geojson"

OUTPUT_STRANDBAEDER_CSV = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/strandbaeder_formatiert.csv"
OUTPUT_STRANDBAEDER_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/strandbaeder_formatiert.geojson"
# =======================================

# Pflichtspalten (case-insensitive)
NAME_KEY = "badname"           # -> properties.name
LINK_KEY = "badestellelink"    # -> properties.info

# Mögliche Koordinaten-Spalten (case-insensitive)
LON_CANDIDATES = {
    "longitude", "lon", "long", "x", "coordinates long",
    "längengrad", "laenge", "geo_lon", "x_wgs84", "xcoord"
}
LAT_CANDIDATES = {
    "latitude", "lat", "y", "coordinates lat",
    "breitengrad", "breite", "geo_lat", "y_wgs84", "ycoord"
}


def sniff_dialect(csv_path: Path):
    """Trennzeichen automatisch erkennen (Fallback: Komma)."""
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        try:
            return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        except Exception:
            class Simple:
                delimiter = ","
            return Simple()


def normalize_headers(headers):
    """Original-Header -> lower-case-Map."""
    return {h: h.strip().lower() for h in headers}


def find_column(header_map, desired_key=None, candidates=None):
    """
    Finde die Original-Headerbezeichnung für:
    - desired_key (exakter lower-case Key) oder
    - irgendeinen Eintrag aus 'candidates' (Set, lower-case).
    """
    inv = {v: k for k, v in header_map.items()}  # lower -> original

    if desired_key and desired_key in inv:
        return inv[desired_key]

    if candidates:
        for cand in candidates:
            if cand in inv:
                return inv[cand]

    return None


def parse_float_any(s):
    """
    Zahl mit Punkt/Komma und evtl. Tausendern erkennen.
    Beispiele:
      '13,14228' -> 13.14228
      '1.234,56' -> 1234.56
      '52.43271' -> 52.43271
    """
    if s is None:
        return None

    if isinstance(s, (int, float)):
        return float(s)

    text = str(s).strip()

    if text == "":
        return None

    num = re.sub(r"[^\d,.\-]", "", text)

    if not num:
        return None

    if "," in num and "." in num:
        # letztes Trennzeichen entscheidet
        if num.rfind(",") > num.rfind("."):
            num = num.replace(".", "").replace(",", ".")
        else:
            num = num.replace(",", "")

        try:
            return float(num)
        except ValueError:
            return None

    if "," in num and "." not in num:
        try:
            return float(num.replace(",", "."))
        except ValueError:
            return None

    try:
        return float(num)
    except ValueError:
        return None
    
def normalize_strandbad_name(name):
    """
    Wandelt z. B.
    'Wannsee, Strandbad' -> 'Strandbad Wannsee'
    um.

    Andere Namen bleiben unverändert.
    """
    name = name.strip()

    match = re.match(r"^(.*?),\s*Strandbad$", name, flags=re.IGNORECASE)

    if match:
        ort = match.group(1).strip()
        return f"Strandbad {ort}"

    return name


def write_geojson(output_path, features):
    """Schreibt eine FeatureCollection als GeoJSON."""
    result = {
        "type": "FeatureCollection",
        "features": features
    }

    out_geo = Path(output_path)
    out_geo.parent.mkdir(parents=True, exist_ok=True)

    with out_geo.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return out_geo


def write_csv(output_path, rows):
    """Schreibt CSV mit der gewünschten Header-Reihenfolge."""
    headers = [
        "type",
        "coordinates long",
        "coordinates lat",
        "category",
        "name",
        "info"
    ]

    out_csv = Path(output_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return out_csv


def main():
    csv_path = Path(INPUT_CSV)

    if not csv_path.exists():
        raise FileNotFoundError(f"Eingabedatei nicht gefunden: {csv_path}")

    dialect = sniff_dialect(csv_path)

    badestellen_features = []
    badestellen_csv_rows = []

    strandbaeder_features = []
    strandbaeder_csv_rows = []

    skipped_rows = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=dialect.delimiter)

        if reader.fieldnames is None:
            raise ValueError("CSV hat keine Headerzeile.")

        header_map = normalize_headers(reader.fieldnames)

        # Spalten bestimmen
        name_col = find_column(header_map, NAME_KEY)
        link_col = find_column(header_map, LINK_KEY)
        lon_col = find_column(header_map, candidates=LON_CANDIDATES)
        lat_col = find_column(header_map, candidates=LAT_CANDIDATES)

        if not name_col:
            raise KeyError(
                f"Spalte '{NAME_KEY}' nicht gefunden. "
                f"Vorhanden: {reader.fieldnames}"
            )

        if not link_col:
            raise KeyError(
                f"Spalte '{LINK_KEY}' nicht gefunden. "
                f"Vorhanden: {reader.fieldnames}"
            )

        if not lon_col or not lat_col:
            raise KeyError(
                "Longitude/Latitude nicht gefunden. Prüfe Spaltennamen.\n"
                f"Gefundene Header: {reader.fieldnames}"
            )

        for row in reader:
            name = (row.get(name_col) or "").strip()
            is_strandbad = "strandbad" in name.lower()

            if is_strandbad:
                name = normalize_strandbad_name(name)

            info_link = (row.get(link_col) or "").strip()
            lon = parse_float_any(row.get(lon_col))
            lat = parse_float_any(row.get(lat_col))

            if name == "" or info_link == "" or lon is None or lat is None:
                skipped_rows += 1
                continue

            if is_strandbad:
                category = "Strandbad"
            else:
                category = "Badestelle"

            # GeoJSON-Feature
            feature = {
                "type": "Feature",
                "properties": {
                    "name": name,
                    "info": None,
                    "category": category
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            }

            # CSV-Zeile
            csv_row = {
                "type": "Feature",
                "coordinates long": lon,
                "coordinates lat": lat,
                "category": category,
                "name": name,
                "info": info_link
            }

            if is_strandbad:
                strandbaeder_features.append(feature)
                strandbaeder_csv_rows.append(csv_row)
            else:
                badestellen_features.append(feature)
                badestellen_csv_rows.append(csv_row)

    # Outputs schreiben
    out_bad_geo = write_geojson(
        OUTPUT_BADESTELLEN_GEOJSON,
        badestellen_features
    )
    out_bad_csv = write_csv(
        OUTPUT_BADESTELLEN_CSV,
        badestellen_csv_rows
    )

    out_strand_geo = write_geojson(
        OUTPUT_STRANDBAEDER_GEOJSON,
        strandbaeder_features
    )
    out_strand_csv = write_csv(
        OUTPUT_STRANDBAEDER_CSV,
        strandbaeder_csv_rows
    )

    print("✔ Fertig!")
    print(f"- Badestellen: {len(badestellen_features)} Features")
    print(f"  GeoJSON: {out_bad_geo}")
    print(f"  CSV:     {out_bad_csv}")
    print(f"- Strandbäder: {len(strandbaeder_features)} Features")
    print(f"  GeoJSON: {out_strand_geo}")
    print(f"  CSV:     {out_strand_csv}")
    print(f"- Übersprungene Zeilen wegen fehlender Pflichtdaten: {skipped_rows}")


if __name__ == "__main__":
    main()