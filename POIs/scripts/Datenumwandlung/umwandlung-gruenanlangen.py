# umwandlung_gruenanlagen_wfs_filter_geomarea.py
import json
import csv
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
import random

import requests
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from shapely.ops import transform as shp_transform
try:
    from shapely.validation import make_valid as shp_make_valid
except Exception:
    shp_make_valid = None

from pyproj import Transformer

# ==== Pfade anpassen ====
WFS_BASE = "https://gdi.berlin.de/services/wfs/gruenanlagen"
OUT_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/gruenanlagen_punkte_gefiltert.geojson"
OUT_CSV     = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/gruenanlagen_punkte_gefiltert.csv"
TYPENAME_OVERRIDE = None  # z.B. "fis:gruenanlagenbestand", falls bekannt
# ========================

# --- Filter-Parameter ---
MIN_AREA_M2 = 600.0           # Flächenschwelle (geometrisch berechnet)
MIN_AREA_PERIM_RATIO = 0.8    # A/P-Schwelle
RANDOM_SEED = 42              # für reproduzierbare Zufallspunkte
# ------------------------

random.seed(RANDOM_SEED)

# Projektion: WGS84 <-> ETRS89 / UTM 33N (m)
to_utm33 = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True).transform
to_wgs84 = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True).transform

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()

def list_featuretypes(xml_text: str):
    root = ET.fromstring(xml_text)
    pairs = []
    for ft in root.findall(".//{*}FeatureType"):
        name  = ft.findtext(".//{*}Name")  or ""
        title = ft.findtext(".//{*}Title") or ""
        pairs.append((name.strip(), title.strip()))
    return pairs

def find_feature_type(wfs_base: str) -> str:
    urls = [
        f"{wfs_base}?service=WFS&request=GetCapabilities&version=2.0.0",
        f"{wfs_base}?service=WFS&request=GetCapabilities&version=1.1.0",
        f"{wfs_base}?service=WFS&request=GetCapabilities",
    ]
    last_xml = None
    for url in urls:
        r = requests.get(url, timeout=60); r.raise_for_status()
        if "<" in r.text[:500]:
            last_xml = r.text; break
    if not last_xml:
        raise RuntimeError("Konnte GetCapabilities nicht laden (keine XML-Antwort).")

    fts = list_featuretypes(last_xml)
    if not fts:
        raise RuntimeError("Keine FeatureTypes in den Capabilities gefunden.")

    candidates = []
    for name, title in fts:
        if any(tok in norm(name)  for tok in ("gruen", "grun")) or \
           any(tok in norm(title) for tok in ("gruen", "grun")):
            candidates.append(name)
    if candidates:
        return candidates[0]

    print("Hinweis: Kein 'gruen/grün' im Namen/Titel gefunden.")
    for n, t in fts:
        print(f" - Name: {n} | Title: {t}")
    raise RuntimeError("Bitte TYPENAME_OVERRIDE setzen.")

def fetch_wfs_geojson(wfs_base: str, typename: str) -> dict:
    attempts = [
        ("2.0.0", "typenames", "application/json"),
        ("2.0.0", "typenames", "json"),
        ("2.0.0", "typenames", "application/json; subtype=geojson"),
        ("1.1.0", "typeName",  "application/json"),
        ("1.1.0", "typeName",  "json"),
        ("1.1.0", "typeName",  "application/json; subtype=geojson"),
    ]
    for version, pname, ofmt in attempts:
        params = {
            "service": "WFS", "version": version, "request": "GetFeature",
            pname: typename, "srsName": "EPSG:4326", "outputFormat": ofmt
        }
        r = requests.get(wfs_base, params=params, timeout=180); r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            continue
    raise RuntimeError("Keine GeoJSON-Antwort vom WFS (alle Fallbacks probiert).")

def geometry_make_valid(g):
    if g is None: return None
    if shp_make_valid is not None:
        try:
            vg = shp_make_valid(g)
            if not vg.is_empty: return vg
        except Exception: pass
    try:
        bg = g.buffer(0)
        if not bg.is_empty: return bg
    except Exception: pass
    return None

def random_point_in_polygon(poly: Polygon, max_tries=200) -> Point:
    minx, miny, maxx, maxy = poly.bounds
    for _ in range(max_tries):
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        p = Point(x, y)
        if p.within(poly):
            return p
    return poly.representative_point()

def contains_spiel(props: dict) -> bool:
    """Filter: alles, was 'spiel' enthält (nicht 'platz' allein, kein 'playground')."""
    fields = ["objartname", "planname", "name", "namenr", "namezusatz", "kennzeich"]
    for k in fields:
        v = props.get(k)
        if not v: continue
        s = norm(str(v))
        s_compact = re.sub(r"[\s\-_\/]+", "", s)
        if "spiel" in s_compact:
            return True
    return False

def total_area_perimeter_metric(geom_metric):
    """Gesamtfläche/-umfang in m² bzw. m (MultiPolygon = Summe aller Teile)."""
    if isinstance(geom_metric, Polygon):
        return geom_metric.area, geom_metric.length
    if isinstance(geom_metric, MultiPolygon):
        a = sum(p.area for p in geom_metric.geoms)
        l = sum(p.length for p in geom_metric.geoms)
        return a, l
    return 0.0, 0.0

def largest_polygon(geom):
    if isinstance(geom, Polygon): return geom
    if isinstance(geom, MultiPolygon):
        polys = [p for p in geom.geoms if isinstance(p, Polygon)]
        return max(polys, key=lambda p: p.area) if polys else None
    return None

def main():
    print("→ Hole Capabilities…")
    typename = TYPENAME_OVERRIDE or find_feature_type(WFS_BASE)
    print(f"  FeatureType: {typename}")

    print("→ Lade Features (GeoJSON)…")
    data = fetch_wfs_geojson(WFS_BASE, typename)
    feats = data.get("features", [])
    if not feats:
        raise RuntimeError("Keine Features vom WFS erhalten.")

    kept = rm_small = rm_ratio = rm_spiel = invalid = 0
    out_features, csv_rows = [], []

    for f in feats:
        geom = f.get("geometry")
        if not geom: continue
        try:
            g = shape(geom)
        except Exception:
            continue

        if not isinstance(g, (Polygon, MultiPolygon)):
            continue

        g = geometry_make_valid(g)
        if g is None or g.is_empty:
            invalid += 1
            continue

        props = f.get("properties", {}) or {}

        # Spiel-Filter
        if contains_spiel(props):
            rm_spiel += 1
            continue

        # Geometrie komplett in metrisches CRS
        g_m = shp_transform(to_utm33, g)
        area_total_m2, perim_total_m = total_area_perimeter_metric(g_m)
        ratio_total = (area_total_m2 / perim_total_m) if perim_total_m > 0 else 0.0

        # Filter 1: Fläche
        if area_total_m2 < MIN_AREA_M2:
            rm_small += 1
            continue

        # Filter 2: A/P
        if ratio_total < MIN_AREA_PERIM_RATIO:
            rm_ratio += 1
            continue

        # Punkt auf Basis größtes Polygon: Zentroid, sonst Innenpunkt
        main_poly = largest_polygon(g)
        if main_poly is None:
            invalid += 1
            continue
        main_poly_m = shp_transform(to_utm33, main_poly)
        c_m = main_poly_m.centroid
        c_wgs = shp_transform(to_wgs84, c_m)
        p_wgs = c_wgs if c_wgs.within(main_poly) else random_point_in_polygon(main_poly)

        # Properties mappen
        name = (str(props.get("namenr") or "").strip() or "Grünanlage")
        info = (str(props.get("namezusatz") or "").strip())

        # --- GeoJSON-Feature (nur Standard-Properties!) ---
        feat_out = {
            "type": "Feature",
            "properties": {
                "name": name,
                "info": info,
                "category": "Grünanlage"
            },
            "geometry": {"type": "Point", "coordinates": [float(p_wgs.x), float(p_wgs.y)]}
        }
        out_features.append(feat_out)

        # --- CSV-Zeile: Standard + zusätzliche Geometrie-Werte ---
        csv_rows.append({
            "type": "Feature",
            "coordinates long": float(p_wgs.x),
            "coordinates lat": float(p_wgs.y),
            "category": "Grünanlage",
            "name": name,
            "info": info,
            "area_total_m2": round(area_total_m2, 2),
            "perimeter_total_m": round(perim_total_m, 2),
            "area_perimeter_ratio_total": round(ratio_total, 4)
        })

        kept += 1

    # Dateien schreiben
    Path(OUT_GEOJSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": out_features}, f, ensure_ascii=False, indent=2)

    headers = [
        "type", "coordinates long", "coordinates lat", "category", "name", "info",
        "area_total_m2", "perimeter_total_m", "area_perimeter_ratio_total"
    ]
    Path(OUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(csv_rows)

    print("✔ Fertig!")
    print(f"  behalten:         {kept}")
    print(f"  entfernt <{MIN_AREA_M2} m²: {rm_small}")
    print(f"  entfernt A/P<{MIN_AREA_PERIM_RATIO}: {rm_ratio}")
    print(f"  entfernt 'spiel': {rm_spiel}")
    print(f"  ungültige Geom.:  {invalid}")
    print(f"GeoJSON: {OUT_GEOJSON}")
    print(f"CSV:     {OUT_CSV}")

if __name__ == "__main__":
    main()
