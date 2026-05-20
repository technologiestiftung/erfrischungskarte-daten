import json
import csv
import re
import math
from pathlib import Path

# ==== Dateien (bei Bedarf anpassen) ====
INPUT_GEOJSONS = [
    "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Brunnen/brunnen-roh.geojson",
    "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Brunnen/zierbrunnen-roh.geojson",
]

OUTPUT_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/brunnen-formatiert.geojson"
OUTPUT_CSV = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/brunnen-formatiert.csv"
OUTPUT_DUPLICATES_CSV = "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Brunnen/brunnen-dubletten-report.csv"

CATEGORY = "Brunnen"

# Punkte innerhalb dieses Radius gelten als Dublette
COORD_DUPLICATE_DISTANCE_M = 2.0


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

    # Fall A: sowohl '.' als auch ',' vorhanden
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')

        try:
            return float(s)
        except ValueError:
            return None

    # Fall B: nur Komma
    if ',' in s:
        s = s.replace('.', '')  # evtl. Tausenderpunkte entfernen
        s = s.replace(',', '.')

        try:
            return float(s)
        except ValueError:
            return None

    # Fall C: nur Punkt
    try:
        return float(s)
    except ValueError:
        return None

def _coords_from_point_bbox(feat):
    """
    Nutzt die bbox als Koordinate, wenn sie einen einzelnen Punkt beschreibt:
    [min_lon, min_lat, max_lon, max_lat]
    und min=max ist.
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

    # Bei Punkt-Features ist die bbox degeneriert: min=max
    if min_lon == max_lon and min_lat == max_lat:
        return [min_lon, min_lat]

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


def _extract_name_info(props):
    """
    Ermittelt name & info aus gängigen Feldern.
    """
    name = None

    for k in ("name", "Name", "title", "ref", "nam", "brunnenbezeichnung"):
        val = _get_nested(props, k)

        if val is not None:
            name = str(val)
            break

    info = None

    for k in ("description", "info", "note", "beschreibung", "remark", "Remark", "standort"):
        val = _get_nested(props, k)

        if val is not None:
            info = str(val)
            break

    return name, info


def _as_features_from_overpass(data):
    """
    Konvertiert Overpass-JSON (elements) in eine Feature-Liste.
    Nutzt center/geometry, wenn vorhanden.
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


def _haversine_m(lon1, lat1, lon2, lat2):
    """
    Berechnet die Distanz zwischen zwei Koordinaten in Metern.
    """
    earth_radius_m = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )

    return 2 * earth_radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _is_duplicate(candidate, existing_features):
    """
    Dublette ausschließlich über Koordinaten.
    Gibt zurück:
    - existing feature
    - Abstand in Metern
    """
    cand_lon, cand_lat = candidate["geometry"]["coordinates"]

    for existing in existing_features:
        ex_lon, ex_lat = existing["geometry"]["coordinates"]

        distance = _haversine_m(cand_lon, cand_lat, ex_lon, ex_lat)

        if distance <= COORD_DUPLICATE_DISTANCE_M:
            return existing, distance

    return None, None


def _merge_duplicate(existing, candidate):
    """
    Bei erkannten Dubletten werden fehlende Angaben ergänzt:
    - Wenn der vorhandene Name nur 'Brunnen' ist und der neue spezifischer,
      wird der spezifischere Name übernommen.
    - Fehlende Info wird ergänzt.
    """
    existing_props = existing["properties"]
    candidate_props = candidate["properties"]

    existing_name = existing_props.get("name")
    candidate_name = candidate_props.get("name")

    if existing_name == "Brunnen" and candidate_name not in (None, "", "Brunnen"):
        existing_props["name"] = candidate_name

    existing_info = existing_props.get("info")
    candidate_info = candidate_props.get("info")

    if not existing_info and candidate_info:
        existing_props["info"] = candidate_info


def _load_features_from_file(path_str):
    path = Path(path_str)

    if not path.exists():
        raise SystemExit(f"Eingabedatei nicht gefunden: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if (
        isinstance(data, dict)
        and data.get("type") == "FeatureCollection"
        and "features" in data
    ):
        features = data["features"]

    elif isinstance(data, dict) and "elements" in data:
        features = _as_features_from_overpass(data)

    else:
        raise SystemExit(
            f"Unbekanntes Format in {path.name}: "
            "Erwartet FeatureCollection oder Overpass-JSON (elements)."
        )

    for feat in features:
        props = feat.setdefault("properties", {})
        props["_source_file"] = path.name

    return features


def main():
    all_input_features = []
    duplicate_report = []

    # Beide GeoJSON-Dateien einlesen und aggregieren
    for input_path in INPUT_GEOJSONS:
        features = _load_features_from_file(input_path)
        all_input_features.extend(features)

    out_features = []

    total_input = len(all_input_features)
    skipped_without_coords = 0
    duplicates_removed = 0

    for feat in all_input_features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry")

        source_file = props.get("_source_file", "")

        # Name/Info ermitteln
        name, info = _extract_name_info(props)

        # Name niemals leer
        if name is None or str(name).strip() == "":
            name = "Brunnen"

        # Falls info nur "Brunnen" enthält -> info = None
        if info is not None and str(info).strip().lower() == "brunnen":
            info = None

        # Koordinaten bestimmen
        # Zuerst prüfen, ob eine punktförmige bbox vorhanden ist.
        source_file = props.get("_source_file", "")

        # Nur bei den Zierbrunnen die bbox verwenden,
        # weil dort geometry.coordinates offenbar fehlerhaft ist.
        if source_file == "zierbrunnen-roh.geojson":
            coords = _coords_from_point_bbox(feat)

            # Fallback, falls bbox unerwartet fehlt
            if coords is None:
                coords = _centroid_geometry(geom)

        # Bei brunnen-roh.geojson die korrekten geometry.coordinates verwenden
        else:
            coords = _centroid_geometry(geom)

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

        candidate = {
            "type": "Feature",
            "properties": {
                "name": name,
                "info": info if info is not None else None,
                "category": CATEGORY,
                "_source_file": source_file
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }

        # Dubletten ausschließlich über Koordinaten prüfen
        duplicate, distance = _is_duplicate(candidate, out_features)

        if duplicate is not None:
            duplicate_report.append({
                "distance_m": round(distance, 3),

                "removed_source": candidate["properties"].get("_source_file", ""),
                "removed_name": candidate["properties"].get("name", ""),
                "removed_lon": candidate["geometry"]["coordinates"][0],
                "removed_lat": candidate["geometry"]["coordinates"][1],

                "kept_source": duplicate["properties"].get("_source_file", ""),
                "kept_name": duplicate["properties"].get("name", ""),
                "kept_lon": duplicate["geometry"]["coordinates"][0],
                "kept_lat": duplicate["geometry"]["coordinates"][1],
            })

            _merge_duplicate(duplicate, candidate)
            duplicates_removed += 1
            continue

        out_features.append(candidate)

    # _source_file vor finalem GeoJSON wieder entfernen
    cleaned_out_features = []

    for feat in out_features:
        cleaned_props = {
            "name": feat["properties"]["name"],
            "info": feat["properties"]["info"],
            "category": feat["properties"]["category"]
        }

        cleaned_out_features.append({
            "type": "Feature",
            "properties": cleaned_props,
            "geometry": feat["geometry"]
        })

    # GeoJSON schreiben
    result = {
        "type": "FeatureCollection",
        "features": cleaned_out_features
    }

    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # CSV-Zeilen vorbereiten
    csv_rows = []

    for feat in cleaned_out_features:
        lon, lat = feat["geometry"]["coordinates"]
        props = feat["properties"]

        csv_rows.append({
            "type": "Point",
            "coordinates long": lon,
            "coordinates lat": lat,
            "category": props["category"],
            "name": props["name"],
            "info": "" if props["info"] is None else str(props["info"])
        })

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

    # Dubletten-Report schreiben
    duplicate_headers = [
        "distance_m",
        "removed_source",
        "removed_name",
        "removed_lon",
        "removed_lat",
        "kept_source",
        "kept_name",
        "kept_lon",
        "kept_lat",
    ]

    with open(OUTPUT_DUPLICATES_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=duplicate_headers)
        writer.writeheader()
        writer.writerows(duplicate_report)

    print(
        "✔ Fertig!\n"
        f"- Eingelesene Datensätze: {total_input}\n"
        f"- Ohne Koordinaten übersprungen: {skipped_without_coords}\n"
        f"- Über Koordinaten erkannte Dubletten entfernt: {duplicates_removed}\n"
        f"- Final ausgegebene Datensätze: {len(cleaned_out_features)}\n"
        f"- Neues GeoJSON: {OUTPUT_GEOJSON}\n"
        f"- CSV: {OUTPUT_CSV}\n"
        f"- Dubletten-Report: {OUTPUT_DUPLICATES_CSV}"
    )


if __name__ == "__main__":
    main()