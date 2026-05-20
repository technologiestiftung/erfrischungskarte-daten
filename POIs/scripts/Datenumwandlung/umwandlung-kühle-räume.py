import json
import csv
import re
from pathlib import Path

# ==== Dateien (bei Bedarf anpassen) ====
INPUT_GEOJSON = "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Kühle-Räume/kuehle_raeume_roh.geojson"
OUTPUT_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/kuehle_raeume_formatiert.geojson"
OUTPUT_CSV = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/kuehle_raeume_formatiert.csv"
# =======================================

CATEGORY = 'Öffentlicher "Kühler Raum"'


def _parse_float_locale(num):
    """
    Robust gegen '.' und ',' als Dezimal-/Tausender-Trennzeichen.
    Gibt float oder None zurück.
    """
    if num is None:
        return None

    if isinstance(num, (int, float)):
        return float(num)

    s = str(num).strip()

    if not s:
        return None

    # nur Ziffern, Komma, Punkt, Minus erlauben
    if not re.match(r"^-?[0-9\.,]+$", s):
        return None

    # A: sowohl '.' als auch ',' -> Heuristik
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')

        try:
            return float(s)
        except ValueError:
            return None

    # B: nur Komma
    if ',' in s:
        s = s.replace('.', '')
        s = s.replace(',', '.')

        try:
            return float(s)
        except ValueError:
            return None

    # C: nur Punkt
    try:
        return float(s)
    except ValueError:
        return None


def _centroid_of_coords(coords):
    """
    Einfache arithmetische Mitte über eine Liste von [lon, lat]-Paaren.
    """
    if not coords:
        return None

    xs = ys = 0.0
    n = 0

    for c in coords:
        if isinstance(c, (list, tuple)) and len(c) >= 2:
            lon = _parse_float_locale(c[0])
            lat = _parse_float_locale(c[1])

            if lon is None or lat is None:
                continue

            xs += lon
            ys += lat
            n += 1

    return [xs / n, ys / n] if n else None


def _centroid_geometry(geom):
    """
    Liefert [lon, lat] für Point / MultiPoint / (Multi)LineString / (Multi)Polygon.
    Für Polygon wird der Außenring gemittelt.
    """
    if not geom or "type" not in geom:
        return None

    gtype = geom["type"]
    coords = geom.get("coordinates")

    if gtype == "Point":
        lon = _parse_float_locale(coords[0]) if coords else None
        lat = _parse_float_locale(coords[1]) if coords else None

        return [lon, lat] if lon is not None and lat is not None else None

    if gtype in ("MultiPoint", "LineString"):
        return _centroid_of_coords(coords or [])

    if gtype == "MultiLineString":
        pts = [pt for line in (coords or []) for pt in line]
        return _centroid_of_coords(pts)

    if gtype == "Polygon":
        if coords and isinstance(coords, list) and len(coords) > 0:
            return _centroid_of_coords(coords[0])  # outer ring
        return None

    if gtype == "MultiPolygon":
        pts = []

        for poly in (coords or []):
            if poly and isinstance(poly, list) and len(poly) > 0:
                pts.extend(poly[0])  # outer ring

        return _centroid_of_coords(pts)

    return None


def _coords_from_point_bbox(feat):
    """
    Nutzt die bbox als Koordinate, wenn sie einen einzelnen Punkt beschreibt:
    [min_lon, min_lat, max_lon, max_lat].

    Für kuehle_raeume_roh.geojson liegen hier die korrekten Koordinaten.
    """
    bbox = feat.get("bbox")

    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return None

    min_lon = _parse_float_locale(bbox[0])
    min_lat = _parse_float_locale(bbox[1])
    max_lon = _parse_float_locale(bbox[2])
    max_lat = _parse_float_locale(bbox[3])

    if None in (min_lon, min_lat, max_lon, max_lat):
        return None

    # bbox muss einen Punkt beschreiben
    if abs(min_lon - max_lon) > 1e-12 or abs(min_lat - max_lat) > 1e-12:
        return None

    # Plausibilitätsprüfung für WGS84
    if not (-180 <= min_lon <= 180 and -90 <= min_lat <= 90):
        return None

    return [min_lon, min_lat]


def _get_nested(props, key):
    """
    Sucht 'key' in properties und, falls vorhanden, in properties['tags'].
    """
    if key in props and props[key] not in ("", None):
        return props[key]

    tags = props.get("tags", {})

    if isinstance(tags, dict) and key in tags and tags[key] not in ("", None):
        return tags[key]

    return None


def _build_info(props):
    """
    Baut das info-Feld im gewünschten Zielformat.
    Mögliche Bestandteile werden mit | getrennt:
    - Adresse
    - Öffnungszeiten
    - Rollstuhlgerechter Zugang
    - Hinweis
    """
    adresse = _clean_text(_get_nested(props, "adresse"))
    oeffnungszeiten = _clean_text(_get_nested(props, "oeffnungszeiten"))
    rollstuhl = _clean_text(_get_nested(props, "rollstuhlgerechter_zugang"))
    hinweis = _clean_text(_get_nested(props, "hinweis"))

    info_parts = []

    if adresse:
        info_parts.append(adresse)

    if oeffnungszeiten:
        info_parts.append(oeffnungszeiten)

    if rollstuhl:
        info_parts.append(rollstuhl)

    if hinweis:
        info_parts.append(hinweis)

    return " | ".join(info_parts) if info_parts else None


def _extract_name_info(props):
    """
    Ermittelt name & info für Kühle Räume.
    """
    name = _clean_text(_get_nested(props, "kuehle_raeume"))
    info = _build_info(props)

    return name if name else None, info


def _as_features_from_overpass(data):
    """
    Konvertiert Overpass-JSON (elements) in eine Feature-Liste.
    Allgemeiner Fallback.
    """
    feats = []

    for el in data.get("elements", []):
        props = {"id": el.get("id")}
        tags = el.get("tags", {})

        if isinstance(tags, dict):
            props.update(tags)

        geom = None

        if el.get("type") == "node":
            lon = _parse_float_locale(el.get("lon"))
            lat = _parse_float_locale(el.get("lat"))

            if lon is not None and lat is not None:
                geom = {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }

        else:
            center = el.get("center")

            if isinstance(center, dict):
                lon = _parse_float_locale(center.get("lon"))
                lat = _parse_float_locale(center.get("lat"))

                if lon is not None and lat is not None:
                    geom = {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }

            if geom is None:
                geom_list = el.get("geometry")

                if isinstance(geom_list, list) and geom_list:
                    pts = [
                        [
                            _parse_float_locale(p.get("lon")),
                            _parse_float_locale(p.get("lat"))
                        ]
                        for p in geom_list
                        if "lon" in p and "lat" in p
                    ]

                    pts = [
                        [lo, la]
                        for lo, la in pts
                        if lo is not None and la is not None
                    ]

                    c = _centroid_of_coords(pts)

                    if c:
                        geom = {
                            "type": "Point",
                            "coordinates": c
                        }

        feats.append({
            "type": "Feature",
            "properties": props,
            "geometry": geom
        })

    return feats

def _clean_text(value):
    """
    Entfernt Zeilenumbrüche und fasst mehrfaches Whitespace zusammen.
    """
    if value is None:
        return ""

    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)

    return text


def main():
    # Eingabe lesen
    src_path = Path(INPUT_GEOJSON)

    if not src_path.exists():
        raise SystemExit(f"Eingabedatei nicht gefunden: {src_path}")

    with src_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Feature-Liste bestimmen
    if (
        isinstance(data, dict)
        and data.get("type") == "FeatureCollection"
        and "features" in data
    ):
        in_features = data["features"]

    elif isinstance(data, dict) and "elements" in data:
        in_features = _as_features_from_overpass(data)

    else:
        raise SystemExit(
            "Unbekanntes Format: "
            "Erwartet FeatureCollection oder Overpass-JSON (elements)."
        )

    out_features = []
    csv_rows = []
    skipped_without_coords = 0

    for feat in in_features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry")

        # Name/Info ermitteln
        name, info = _extract_name_info(props)

        # Name niemals leer
        if name is None or str(name).strip() == "":
            name = "Kühler Raum"

        # Koordinaten:
        # In kuehle_raeume_roh.geojson stehen die korrekten WGS84-Koordinaten in bbox.
        coords = _coords_from_point_bbox(feat)

        # Fallback auf geometry, falls bbox fehlt
        if coords is None:
            coords = _centroid_geometry(geom)

        # weiterer Fallback: lon/lat in Properties
        if coords is None:
            lon_prop = _get_nested(props, "lon") or props.get("longitude")
            lat_prop = _get_nested(props, "lat") or props.get("latitude")

            lon = _parse_float_locale(lon_prop)
            lat = _parse_float_locale(lat_prop)

            if lon is not None and lat is not None:
                coords = [lon, lat]

        # Ohne Koordinaten überspringen
        if coords is None or any(v is None for v in coords[:2]):
            skipped_without_coords += 1
            continue

        lon, lat = float(coords[0]), float(coords[1])

        # GeoJSON-Feature im Zielformat
        out_feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "category": CATEGORY,
                "name": name,
                "info": info if info is not None else None
            }
        }

        out_features.append(out_feat)

        # CSV-Zeile
        csv_rows.append({
            "type": "Point",
            "coordinates long": lon,
            "coordinates lat": lat,
            "category": CATEGORY,
            "name": name,
            "info": "" if info is None else str(info)
        })

    # GeoJSON schreiben
    result = {
        "type": "FeatureCollection",
        "features": out_features
    }

    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # CSV schreiben
    headers = [
        "type",
        "coordinates long",
        "coordinates lat",
        "category",
        "name",
        "info"
    ]

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(
        "✔ Fertig!\n"
        f"- Eingelesene Datensätze: {len(in_features)}\n"
        f"- Ohne Koordinaten übersprungen: {skipped_without_coords}\n"
        f"- Final ausgegebene Datensätze: {len(out_features)}\n"
        f"- Neues GeoJSON: {OUTPUT_GEOJSON}\n"
        f"- CSV: {OUTPUT_CSV}"
    )


if __name__ == "__main__":
    main()