import json
import csv
import re
from pathlib import Path

# ==== Dateien (bei Bedarf anpassen) ====
INPUT_GEOJSON = "/Users/norahunger/Documents/ODIS/Erfrischungskarte/2026/Toiletten/toiletten_toiletten_WGS84.geojson"
OUTPUT_GEOJSON = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/GeoJSON/toiletten_formatiert.geojson"
OUTPUT_CSV = "/Users/norahunger/Documents/GitHub/erfrischungskarte-daten/POIs/single-files/2026/CSV/toiletten_formatiert.csv"
# =======================================

def format_barrierefreiheit(value):
    """
    True / 'ja' / 'true' / '1' -> 'barrierefrei'
    sonst -> 'nicht barrierefrei/unbekannt'
    """
    if value is True:
        return "barrierefrei"
    if isinstance(value, str) and value.strip().lower() in {"ja", "true", "1"}:
        return "barrierefrei"
    return "nicht barrierefrei/unbekannt"

def _to_float_from_string(s: str):
    """
    Versucht, eine Zahl aus einem String zu extrahieren und korrekt zu interpretieren,
    egal ob '.' oder ',' als Dezimaltrennzeichen benutzt werden.
    Behandelt auch Fälle wie '1.234,56' oder '1,234.56'.
    """
    s_clean = s.strip()

    # Schnell-Check: kostenlos
    if any(w in s_clean.lower() for w in ["kostenfrei", "kostenlos", "gratis", "free", "ohne gebühr"]):
        return 0.0

    # Nur Ziffern/Trennzeichen extrahieren (inkl. € entfernen)
    s_num = re.sub(r"[^\d,.\-]", "", s_clean)

    if not s_num:
        return None

    # Fall A: sowohl '.' als auch ',' vorhanden -> heuristik
    if ',' in s_num and '.' in s_num:
        # Wenn das letzte Trennzeichen ein Komma ist, interpretieren wir ',' als Dezimaltrennzeichen (deutsch)
        if s_num.rfind(',') > s_num.rfind('.'):
            # Tausenderpunkte entfernen, Komma -> Punkt
            s_num = s_num.replace('.', '')
            s_num = s_num.replace(',', '.')
        else:
            # Letztes Trennzeichen ist Punkt -> englisch: Kommas als Tausender entfernen
            s_num = s_num.replace(',', '')
        # danach bleibt eine Punkt-Zahl übrig
        try:
            return float(s_num)
        except ValueError:
            pass

    # Fall B: nur Komma vorhanden -> Komma als Dezimaltrennzeichen
    if ',' in s_num and '.' not in s_num:
        try:
            return float(s_num.replace(',', '.'))
        except ValueError:
            pass

    # Fall C: nur Punkt oder reine Ziffern
    try:
        return float(s_num)
    except ValueError:
        # Fallback: erste "einfache" Zahl greifen
        m = re.search(r"\d+(?:[.,]\d+)?", s_clean)
        if m:
            return _to_float_from_string(m.group(0))
    return None

def _format_eur_two_decimals(value_float: float) -> str:
    """
    Formatiert einen float als 'X,YY €' (immer zwei Nachkommastellen, Komma als Dezimaltrennzeichen).
    """
    s = f"{value_float:.2f}"      # -> '0.50'
    s = s.replace('.', ',')       # -> '0,50'
    return f"{s} €"

def format_nutzungsentgelt(raw_value):
    """
    Formatiert das Feld 'nutzungsentgelt' sauber:
    - None/leer/„unbekannt“ -> 'unbekannt'
    - kostenlose Schlüsselwörter -> '0,00 €'
    - Zahlen (int/float oder im Text) -> 'X,YY €'
    - vorhandenes '€' wird ignoriert und sauber neu formatiert
    """
    if raw_value is None:
        return "unbekannt"

    # numerisch direkt
    if isinstance(raw_value, (int, float)):
        return _format_eur_two_decimals(float(raw_value))

    s = str(raw_value).strip()
    if s == "" or s.lower() in {"unbekannt", "n/a", "na", "-"}:
        return "unbekannt"

    # kostenlos
    if any(w in s.lower() for w in ["kostenfrei", "kostenlos", "gratis", "free", "ohne gebühr"]):
        return _format_eur_two_decimals(0.0)

    # Zahl extrahieren & formatieren
    num = _to_float_from_string(s)
    if num is not None:
        return _format_eur_two_decimals(num)

    # Keine Zahl erkennbar -> als Text zurück (selten)
    return s

def main():
    # Datei prüfen
    if not Path(INPUT_GEOJSON).exists():
        raise FileNotFoundError(f"Eingabedatei nicht gefunden: {INPUT_GEOJSON}")

    # GeoJSON einlesen
    with open(INPUT_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_features = []
    csv_rows = []

    for feature in data.get("features", []):
        # geom = feature.get("geometry", {}) or {}
        coords = feature.get("bbox", [None, None])[:2]
        if not coords or len(coords) < 2:
            # ungültige/fehlende Punkt-Geometrie
            continue

        props = feature.get("properties", {}) or {}

        barrierefrei_text = format_barrierefreiheit(props.get("barrierefrei"))
        preis_fmt = format_nutzungsentgelt(props.get("nutzungsentgelt"))
        info = f"{barrierefrei_text}, Preis: {preis_fmt}"

        # Neues Feature (Ziel-Format)
        new_feature = {
            "type": "Feature",
            "properties": {
                "name": "Öffentliche Toilette",
                "info": info,
                "category": "Toilette"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [coords[0], coords[1]]
            }
        }
        new_features.append(new_feature)

        # CSV-Zeile mit gewünschten Spalten
        csv_rows.append({
            "type": "Feature",
            "coordinates long": coords[0],
            "coordinates lat": coords[1],
            "category": "Toilette",
            "name": "Öffentliche Toilette",
            "info": info
        })

    # Neues GeoJSON speichern
    result = {
        "type": "FeatureCollection",
        "features": new_features
    }
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # CSV speichern (genaue Header-Reihenfolge)
    headers = ["type", "coordinates long", "coordinates lat", "category", "name", "info"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✔ Fertig!\n- Neues GeoJSON: {OUTPUT_GEOJSON}\n- CSV: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
