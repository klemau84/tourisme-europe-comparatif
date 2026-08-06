from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
# Deux ans de recul garantissent une année commune complète pour les indicateurs
# de fréquentation, capacité, occupation, prix et population.
YEAR = str(datetime.now(timezone.utc).year - 2)
COUNTRIES = {
    "ES": "Espagne", "FR": "France", "IT": "Italie", "DE": "Allemagne",
    "PT": "Portugal", "EL": "Grèce", "HR": "Croatie", "AT": "Autriche",
    "NL": "Pays-Bas", "BE": "Belgique", "IE": "Irlande", "DK": "Danemark",
    "SE": "Suède", "CZ": "Tchéquie", "PL": "Pologne",
}


def fetch(dataset: str, **params: object) -> dict:
    query = [("lang", "en")]
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            query.extend((key, item) for item in value)
        else:
            query.append((key, value))
    url = f"{API}/{dataset}?{urlencode(query)}"
    req = Request(url, headers={"User-Agent": "TourismeEuropeComparatif/1.0"})
    with urlopen(req, timeout=90) as response:
        return json.load(response)


def jsonstat_rows(payload: dict) -> pd.DataFrame:
    dims = payload["id"]
    sizes = payload["size"]
    labels: list[list[str]] = []
    for dim in dims:
        index = payload["dimension"][dim]["category"]["index"]
        if isinstance(index, dict):
            ordered = [key for key, _ in sorted(index.items(), key=lambda item: item[1])]
        else:
            ordered = list(index)
        labels.append(ordered)

    rows = []
    for flat_index, coordinates in enumerate(product(*labels)):
        value = payload.get("value", {}).get(str(flat_index))
        if value is None:
            continue
        row = dict(zip(dims, coordinates))
        row["value"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def indicator(dataset: str, value_name: str, **filters: object) -> pd.DataFrame:
    payload = fetch(dataset, time=YEAR, geo=list(COUNTRIES), **filters)
    frame = jsonstat_rows(payload)
    return frame[["geo", "value"]].rename(columns={"value": value_name})


def main() -> None:
    DATA.mkdir(exist_ok=True)
    base = pd.DataFrame({"code": list(COUNTRIES), "pays": list(COUNTRIES.values())})

    frames = [
        indicator("tour_occ_ninat", "nuitees_total", unit="NR", c_resid="TOTAL", nace_r2="I551-I553"),
        indicator("tour_occ_ninat", "nuitees_etrangeres", unit="NR", c_resid="FOR", nace_r2="I551-I553"),
        indicator("tour_occ_arnat", "arrivees_total", unit="NR", c_resid="TOTAL", nace_r2="I551-I553"),
        indicator("tour_occ_arnat", "arrivees_etrangeres", unit="NR", c_resid="FOR", nace_r2="I551-I553"),
        indicator("tour_cap_nat", "lits_touristiques", unit="NR", accomunit="BEDPL", nace_r2="I551-I553"),
        indicator("tour_occ_anor", "occupation_hotels_pct", unit="PC", accomunit="BEDRM", hotelsize="TOTAL"),
        indicator("prc_ppp_ind", "indice_prix_restaurants_hotels", na_item="PLI_EU27_2020", ppp_cat="A0111"),
        indicator("demo_pjan", "population", unit="NR", sex="T", age="TOTAL"),
    ]
    previous = fetch(
        "tour_occ_ninat", time="2023", geo=list(COUNTRIES), unit="NR",
        c_resid="TOTAL", nace_r2="I551-I553",
    )
    frames.append(
        jsonstat_rows(previous)[["geo", "value"]].rename(columns={"value": "nuitees_2023"})
    )

    result = base.rename(columns={"code": "geo"})
    for frame in frames:
        result = result.merge(frame, on="geo", how="left")

    numeric = [col for col in result.columns if col not in ["geo", "pays"]]
    result[numeric] = result[numeric].apply(pd.to_numeric, errors="coerce")
    result["part_etrangere_pct"] = 100 * result["nuitees_etrangeres"] / result["nuitees_total"]
    result["duree_moyenne_nuits"] = result["nuitees_total"] / result["arrivees_total"]
    result["nuitees_par_habitant"] = result["nuitees_total"] / result["population"]
    result["lits_pour_1000_habitants"] = 1000 * result["lits_touristiques"] / result["population"]
    result["evolution_nuitees_pct"] = 100 * (result["nuitees_total"] / result["nuitees_2023"] - 1)
    result["annee"] = int(YEAR)

    ordered = [
        "geo", "pays", "annee", "nuitees_total", "nuitees_etrangeres",
        "arrivees_total", "arrivees_etrangeres", "part_etrangere_pct",
        "duree_moyenne_nuits", "nuitees_par_habitant", "lits_touristiques",
        "lits_pour_1000_habitants", "occupation_hotels_pct",
        "indice_prix_restaurants_hotels", "evolution_nuitees_pct", "population",
    ]
    result[ordered].to_csv(DATA / "comparatif_pays.csv", index=False, encoding="utf-8-sig")

    metadata = pd.DataFrame([
        ["version", "V1.0"],
        ["annee_reference", YEAR],
        ["date_actualisation_utc", datetime.now(timezone.utc).replace(microsecond=0).isoformat()],
        ["source_principale", "Eurostat"],
        ["nombre_pays", str(len(result))],
    ], columns=["cle", "valeur"])
    metadata.to_csv(DATA / "metadonnees.csv", index=False, encoding="utf-8-sig")
    print(f"Données Eurostat {YEAR} actualisées pour {len(result)} pays.")


if __name__ == "__main__":
    main()
