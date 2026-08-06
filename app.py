from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent
DATA = ROOT / "data"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    countries = pd.read_csv(DATA / "comparatif_pays.csv")
    readings = pd.read_csv(DATA / "lectures_pays.csv").fillna("")
    sources = pd.read_csv(DATA / "sources.csv")
    metadata_frame = pd.read_csv(DATA / "metadonnees.csv")
    metadata = dict(zip(metadata_frame["cle"], metadata_frame["valeur"].astype(str)))
    return countries, readings, sources, metadata


def millions(value: float) -> str:
    return f"{value / 1_000_000:.1f} M".replace(".", ",")


def delta_text(value: float) -> str:
    return f"{value:+.1f} %".replace(".", ",")


def index_comment(value: float) -> str:
    difference = value - 100
    if abs(difference) < 1:
        return "proche de la moyenne de l'Union européenne"
    direction = "au-dessus" if difference > 0 else "en dessous"
    return f"{abs(difference):.1f} % {direction} de la moyenne de l'UE".replace(".", ",")


st.set_page_config(
    page_title="Tourisme Europe comparatif",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {
        background: rgba(127,127,127,.10);
        border: 1px solid rgba(127,127,127,.24);
        border-radius: 12px;
        padding: 14px;
    }
    .insight {
        border-left: 5px solid #ef6c3e;
        background: rgba(239,108,62,.10);
        padding: 14px 18px;
        border-radius: 8px;
        margin: 10px 0 18px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

df, readings_df, sources_df, metadata = load_data()
year = metadata.get("annee_reference", "2024")

st.title("Tourisme en Europe · fréquentation et compétitivité")
st.caption(
    "Comparer les volumes ne suffit pas : cette V1 croise les nuitées, la durée des séjours, "
    "la clientèle étrangère, l'hébergement, l'occupation et les prix."
)

with st.sidebar:
    st.header("Sélection")
    chosen = st.multiselect(
        "Pays affichés",
        df["pays"].tolist(),
        default=df["pays"].tolist(),
    )
    ranking_indicator = st.selectbox(
        "Classement principal",
        [
            "Nuitées totales",
            "Nuitées étrangères",
            "Nuitées par habitant",
            "Durée moyenne",
            "Occupation hôtelière",
            "Prix restaurants et hôtels",
        ],
    )
    st.divider()
    st.caption(
        f"Données annuelles {year} · Eurostat · version {metadata.get('version', 'V1.0')}"
    )

filtered = df[df["pays"].isin(chosen)].copy()
if filtered.empty:
    st.warning("Sélectionnez au moins un pays.")
    st.stop()

tab_overview, tab_duel, tab_reasons, tab_prices, tab_data, tab_sources = st.tabs(
    [
        "Vue européenne", "France vs Espagne", "Pourquoi ces écarts ?",
        "Hébergements & prix", "Données détaillées", "Méthode & sources",
    ]
)

indicator_map = {
    "Nuitées totales": ("nuitees_total", "Nuitées", 1_000_000),
    "Nuitées étrangères": ("nuitees_etrangeres", "Nuitées étrangères", 1_000_000),
    "Nuitées par habitant": ("nuitees_par_habitant", "Nuitées par habitant", 1),
    "Durée moyenne": ("duree_moyenne_nuits", "Nuits par arrivée", 1),
    "Occupation hôtelière": ("occupation_hotels_pct", "Occupation des chambres (%)", 1),
    "Prix restaurants et hôtels": ("indice_prix_restaurants_hotels", "Indice UE=100", 1),
}

with tab_overview:
    top = filtered.loc[filtered["nuitees_total"].idxmax()]
    foreign_top = filtered.loc[filtered["nuitees_etrangeres"].idxmax()]
    intensity_top = filtered.loc[filtered["nuitees_par_habitant"].idxmax()]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leader en nuitées", top["pays"], millions(top["nuitees_total"]))
    c2.metric("Leader clientèle étrangère", foreign_top["pays"], millions(foreign_top["nuitees_etrangeres"]))
    c3.metric("Plus forte intensité", intensity_top["pays"], f"{intensity_top['nuitees_par_habitant']:.1f} nuits/hab.")
    c4.metric("Nuitées des pays affichés", millions(filtered["nuitees_total"].sum()))

    column, label, divisor = indicator_map[ranking_indicator]
    ranking = filtered[["pays", column]].sort_values(column, ascending=False).set_index("pays")
    ranking[label] = ranking[column] / divisor
    st.subheader(f"Classement · {ranking_indicator.lower()}")
    st.bar_chart(ranking[[label]])

    st.subheader("Lecture multi-indicateurs")
    overview = filtered.copy()
    overview["nuitees_millions"] = overview["nuitees_total"] / 1_000_000
    overview["nuitees_etrangeres_millions"] = overview["nuitees_etrangeres"] / 1_000_000
    st.dataframe(
        overview.sort_values("nuitees_total", ascending=False)[
            ["pays", "nuitees_millions", "nuitees_etrangeres_millions",
             "part_etrangere_pct", "duree_moyenne_nuits", "nuitees_par_habitant",
             "occupation_hotels_pct", "evolution_nuitees_pct"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "pays": "Pays",
            "nuitees_millions": st.column_config.NumberColumn("Nuitées (M)", format="%.1f"),
            "nuitees_etrangeres_millions": st.column_config.NumberColumn("Étrangères (M)", format="%.1f"),
            "part_etrangere_pct": st.column_config.ProgressColumn("Part étrangère", min_value=0, max_value=100, format="%.1f %%"),
            "duree_moyenne_nuits": st.column_config.NumberColumn("Durée moyenne", format="%.2f nuits"),
            "nuitees_par_habitant": st.column_config.NumberColumn("Nuitées/hab.", format="%.1f"),
            "occupation_hotels_pct": st.column_config.NumberColumn("Occupation hôtels", format="%.1f %%"),
            "evolution_nuitees_pct": st.column_config.NumberColumn("Évolution annuelle", format="%+.1f %%"),
        },
    )

with tab_duel:
    france = df[df["geo"] == "FR"].iloc[0]
    spain = df[df["geo"] == "ES"].iloc[0]
    st.subheader("Le paradoxe France–Espagne")
    st.markdown(
        f"""
        <div class="insight"><b>L'Espagne ne gagne pas sur tous les volumes, mais elle transforme mieux les arrivées en nuitées.</b><br>
        En {year}, elle totalise {millions(spain['nuitees_total'])} de nuitées contre {millions(france['nuitees_total'])} en France,
        avec une durée moyenne de {spain['duree_moyenne_nuits']:.2f} nuits contre {france['duree_moyenne_nuits']:.2f}.
        </div>
        """,
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Avantage nuitées Espagne", millions(spain["nuitees_total"] - france["nuitees_total"]))
    d2.metric("Clientèle étrangère", f"{spain['part_etrangere_pct']:.1f} % ES", f"France {france['part_etrangere_pct']:.1f} %")
    d3.metric("Occupation hôtelière", f"{spain['occupation_hotels_pct']:.1f} % ES", f"France {france['occupation_hotels_pct']:.1f} %")
    d4.metric("Indice de prix", f"{spain['indice_prix_restaurants_hotels']:.1f} ES", f"France {france['indice_prix_restaurants_hotels']:.1f}")

    comparison = pd.DataFrame({
        "Indicateur": [
            "Nuitées totales (millions)", "Nuitées étrangères (millions)",
            "Arrivées en hébergements (millions)", "Durée moyenne (nuits)",
            "Nuitées par habitant", "Places-lits / 1 000 habitants",
            "Occupation des chambres (%)", "Prix restaurants-hôtels (UE=100)",
        ],
        "Espagne": [
            spain["nuitees_total"] / 1e6, spain["nuitees_etrangeres"] / 1e6,
            spain["arrivees_total"] / 1e6, spain["duree_moyenne_nuits"],
            spain["nuitees_par_habitant"], spain["lits_pour_1000_habitants"],
            spain["occupation_hotels_pct"], spain["indice_prix_restaurants_hotels"],
        ],
        "France": [
            france["nuitees_total"] / 1e6, france["nuitees_etrangeres"] / 1e6,
            france["arrivees_total"] / 1e6, france["duree_moyenne_nuits"],
            france["nuitees_par_habitant"], france["lits_pour_1000_habitants"],
            france["occupation_hotels_pct"], france["indice_prix_restaurants_hotels"],
        ],
    })
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    st.markdown("#### Ce que les données suggèrent")
    st.write(
        "L'Espagne bénéficie simultanément d'une clientèle étrangère plus dominante, de séjours plus longs, "
        "d'une meilleure occupation hôtelière et d'un niveau de prix restaurants-hôtels sensiblement inférieur. "
        "La France dispose pourtant de davantage de places-lits et enregistre plus d'arrivées dans les hébergements : "
        "son problème comparatif est moins l'attraction initiale que la durée et la conversion en nuitées."
    )

with tab_reasons:
    st.subheader("Facteurs explicatifs")
    selected_country = st.selectbox("Analyser un pays", filtered["pays"].tolist())
    country = filtered[filtered["pays"] == selected_country].iloc[0]
    reading = readings_df[readings_df["geo"] == country["geo"]].iloc[0]

    r1, r2, r3 = st.columns(3)
    r1.metric("Durée moyenne", f"{country['duree_moyenne_nuits']:.2f} nuits")
    r2.metric("Part étrangère", f"{country['part_etrangere_pct']:.1f} %")
    r3.metric("Évolution des nuitées", delta_text(country["evolution_nuitees_pct"]))

    st.markdown(f"<div class='insight'><b>Lecture :</b> {reading['lecture']}</div>", unsafe_allow_html=True)
    factors = pd.DataFrame([
        ["Positionnement", reading["positionnement"]],
        ["Hébergements", reading["hebergement"]],
        ["Prix", f"{reading['prix']} — indice mesuré : {country['indice_prix_restaurants_hotels']:.1f}, soit {index_comment(country['indice_prix_restaurants_hotels'])}."],
        ["Accessibilité", reading["accessibilite"]],
        ["Accueil / expérience", reading["accueil_experience"]],
    ], columns=["Facteur", "Lecture"])
    st.dataframe(factors, use_container_width=True, hide_index=True)
    st.warning(
        "La V1 ne fabrique pas de note d'accueil. Les avis en ligne, les classements éditoriaux et les impressions "
        "nationales ne constituent pas une mesure homogène. Cet axe sera ajouté uniquement avec une enquête "
        "comparable, datée et documentée."
    )

with tab_prices:
    st.subheader("Capacité, remplissage et prix")
    h1, h2 = st.columns(2)
    with h1:
        st.markdown("#### Prix restaurants et hôtels")
        price_chart = filtered.set_index("pays")[["indice_prix_restaurants_hotels"]].sort_values("indice_prix_restaurants_hotels")
        price_chart.columns = ["Indice UE=100"]
        st.bar_chart(price_chart)
    with h2:
        st.markdown("#### Places-lits pour 1 000 habitants")
        capacity_chart = filtered.set_index("pays")[["lits_pour_1000_habitants"]].sort_values("lits_pour_1000_habitants")
        capacity_chart.columns = ["Places-lits / 1 000 hab."]
        st.bar_chart(capacity_chart)

    st.info(
        "Un prix bas n'entraîne pas automatiquement une forte fréquentation. Il devient un avantage lorsqu'il est "
        "combiné à une capacité suffisante, une bonne accessibilité, un produit touristique lisible et une saison assez longue."
    )

with tab_data:
    st.subheader("Base comparable complète")
    raw = filtered.sort_values("nuitees_total", ascending=False).copy()
    st.dataframe(raw, use_container_width=True, hide_index=True)
    st.download_button(
        "Télécharger la sélection CSV",
        raw.to_csv(index=False).encode("utf-8-sig"),
        f"tourisme_europe_{year}.csv",
        "text/csv",
    )

with tab_sources:
    st.subheader("Méthode")
    st.write(
        "Les indicateurs de fréquentation correspondent aux arrivées et nuitées enregistrées dans les hôtels, "
        "hébergements de courte durée et campings déclarés à Eurostat. Ils ne sont pas équivalents aux passages "
        "aux frontières ni au nombre de personnes uniques."
    )
    st.write(
        "L'indice de prix compare le niveau des restaurants et hôtels entre pays, avec une moyenne UE égale à 100. "
        "Il mesure un niveau relatif, pas le prix précis d'une chambre pendant la haute saison."
    )
    st.dataframe(
        sources_df,
        use_container_width=True,
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("Lien direct")},
    )
    st.caption(f"Dernière extraction : {metadata.get('date_actualisation_utc', 'N/D')}")
