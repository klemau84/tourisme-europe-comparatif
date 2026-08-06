from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent
DATA = ROOT / "data"


@st.cache_data
def load_data():
    countries = pd.read_csv(DATA / "comparatif_pays.csv")
    readings = pd.read_csv(DATA / "lectures_pays.csv").fillna("")
    sources = pd.read_csv(DATA / "sources.csv")
    history = pd.read_csv(DATA / "evolution_annuelle.csv", dtype={"annee": str})
    monthly = pd.read_csv(DATA / "saisonnalite_mensuelle.csv")
    seasonality = pd.read_csv(DATA / "indicateurs_saisonnalite.csv")
    accommodation = pd.read_csv(DATA / "types_hebergement.csv")
    regions = pd.read_csv(DATA / "regions_france_espagne.csv")
    detailed_prices = pd.read_csv(DATA / "prix_detailles_officiels.csv")
    budget = pd.read_csv(DATA / "budget_scenario.csv")
    metadata_frame = pd.read_csv(DATA / "metadonnees.csv")
    metadata = dict(zip(metadata_frame["cle"], metadata_frame["valeur"].astype(str)))
    return (
        countries, readings, sources, history, monthly, seasonality,
        accommodation, regions, detailed_prices, budget, metadata,
    )


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

(
    df, readings_df, sources_df, history_df, monthly_df, seasonality_df,
    accommodation_df, regions_df, detailed_prices_df, budget_df, metadata,
) = load_data()
year = metadata.get("annee_reference", "2024")

st.title("Tourisme en Europe · fréquentation et compétitivité")
st.caption(
    "La V3.1 place les tarifs indicatifs en euros au premier plan et ajoute un budget de séjour simulé "
    "pour la France, l'Espagne et l'Italie."
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
        f"Données annuelles {year} · Eurostat · version {metadata.get('version', 'V2.0')}"
    )

filtered = df[df["pays"].isin(chosen)].copy()
if filtered.empty:
    st.warning("Sélectionnez au moins un pays.")
    st.stop()

(
    tab_budget, tab_overview, tab_duel, tab_history, tab_seasonality, tab_regions,
    tab_reasons, tab_prices, tab_data, tab_sources,
) = st.tabs(
    [
        "Tarifs en €", "Vue européenne", "France vs Espagne", "Évolution 2019–2024",
        "Saisonnalité", "Régions France–Espagne", "Pourquoi ces écarts ?",
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

    es_season = seasonality_df[seasonality_df["geo"] == "ES"].iloc[0]
    fr_season = seasonality_df[seasonality_df["geo"] == "FR"].iloc[0]
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Avantage nuitées Espagne", millions(spain["nuitees_total"] - france["nuitees_total"]))
    d2.metric("Clientèle étrangère", f"{spain['part_etrangere_pct']:.1f} % ES", f"France {france['part_etrangere_pct']:.1f} %")
    d3.metric("Occupation hôtelière", f"{spain['occupation_hotels_pct']:.1f} % ES", f"France {france['occupation_hotels_pct']:.1f} %")
    d4.metric("Indice de prix", f"{spain['indice_prix_restaurants_hotels']:.1f} ES", f"France {france['indice_prix_restaurants_hotels']:.1f}")
    d5.metric("3 mois les plus forts", f"{es_season['part_3_mois_forts_pct']:.1f} % ES", f"France {fr_season['part_3_mois_forts_pct']:.1f} %")

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

    st.markdown("#### Structure des hébergements")
    duel_accommodation = accommodation_df[accommodation_df["geo"].isin(["ES", "FR"])].set_index("pays")
    duel_accommodation = duel_accommodation[
        ["part_hotels_pct", "part_locations_courte_duree_pct", "part_campings_pct"]
    ].rename(columns={
        "part_hotels_pct": "Hôtels",
        "part_locations_courte_duree_pct": "Locations courte durée",
        "part_campings_pct": "Campings",
    })
    st.bar_chart(duel_accommodation)

with tab_history:
    st.subheader("Évolution des nuitées depuis 2019")
    selected_history = st.multiselect(
        "Pays à comparer dans le temps",
        filtered["pays"].tolist(),
        default=[p for p in ["Espagne", "France", "Italie", "Allemagne"] if p in filtered["pays"].tolist()],
        key="history_countries",
    )
    history_view = history_df[history_df["pays"].isin(selected_history)].copy()
    if history_view.empty:
        st.info("Sélectionnez au moins un pays.")
    else:
        mode = st.radio(
            "Affichage",
            ["Indice 2019 = 100", "Nuitées en millions"],
            horizontal=True,
        )
        if mode == "Indice 2019 = 100":
            chart = history_view.pivot(index="annee", columns="pays", values="indice_2019_100")
            st.line_chart(chart)
            st.caption("100 correspond au niveau de 2019 pour chaque pays. Cette vue compare la vitesse de reprise, pas la taille des marchés.")
        else:
            chart = history_view.assign(nuitees_millions=history_view["nuitees_total"] / 1e6).pivot(
                index="annee", columns="pays", values="nuitees_millions"
            )
            st.line_chart(chart)

        latest_indices = history_view[history_view["annee"] == str(year)].sort_values("indice_2019_100", ascending=False)
        st.dataframe(
            latest_indices[["pays", "nuitees_total", "indice_2019_100"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "pays": "Pays",
                "nuitees_total": st.column_config.NumberColumn(f"Nuitées {year}", format="%,d"),
                "indice_2019_100": st.column_config.NumberColumn("Indice 2019=100", format="%.1f"),
            },
        )

with tab_seasonality:
    st.subheader(f"Saisonnalité mensuelle · {year}")
    selected_season = st.multiselect(
        "Pays à comparer mois par mois",
        filtered["pays"].tolist(),
        default=[p for p in ["Espagne", "France"] if p in filtered["pays"].tolist()],
        key="season_countries",
    )
    monthly_view = monthly_df[monthly_df["pays"].isin(selected_season)].copy()
    if monthly_view.empty:
        st.info("Sélectionnez au moins un pays.")
    else:
        month_labels = {
            1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin",
            7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc",
        }
        monthly_view["libelle_mois"] = monthly_view["numero_mois"].map(month_labels)
        chart = monthly_view.pivot(index="numero_mois", columns="pays", values="part_annuelle_pct")
        chart.index = [month_labels[int(month)] for month in chart.index]
        st.line_chart(chart)
        st.caption("Chaque courbe totalise 100 %. Elle montre la concentration du tourisme dans l'année indépendamment de la taille du pays.")

        indicators = seasonality_df[seasonality_df["pays"].isin(selected_season)].sort_values(
            "part_3_mois_forts_pct", ascending=False
        )
        st.dataframe(
            indicators[["pays", "part_3_mois_forts_pct", "part_juin_aout_pct", "mois_pic", "nuitees_mois_pic"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "pays": "Pays",
                "part_3_mois_forts_pct": st.column_config.ProgressColumn("3 mois les plus forts", min_value=0, max_value=100, format="%.1f %%"),
                "part_juin_aout_pct": st.column_config.NumberColumn("Part juin-août", format="%.1f %%"),
                "mois_pic": "Mois de pointe",
                "nuitees_mois_pic": st.column_config.NumberColumn("Nuitées du mois de pointe", format="%,d"),
            },
        )

with tab_regions:
    st.subheader("Régions touristiques françaises et espagnoles")
    st.caption("Comparaison NUTS 2 : elle évite de réduire les performances nationales aux seules moyennes de pays.")
    region_country = st.radio("Territoire", ["France et Espagne", "France", "Espagne"], horizontal=True)
    regions_view = regions_df.copy()
    if region_country != "France et Espagne":
        regions_view = regions_view[regions_view["pays"] == region_country]
    top_n = st.slider("Nombre de régions affichées", 5, 30, 15)
    region_chart = regions_view.nlargest(top_n, "nuitees_total").copy()
    region_chart["nuitees_millions"] = region_chart["nuitees_total"] / 1e6
    st.bar_chart(region_chart.set_index("region")[["nuitees_millions"]])
    st.dataframe(
        region_chart[["pays", "region", "nuitees_total"]],
        use_container_width=True,
        hide_index=True,
        column_config={"nuitees_total": st.column_config.NumberColumn("Nuitées", format="%,d")},
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
        "La V2 ne fabrique pas de note d'accueil. Les avis en ligne, les classements éditoriaux et les impressions "
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

    st.markdown("#### Répartition des nuitées par type d'hébergement")
    accommodation_view = accommodation_df[accommodation_df["pays"].isin(chosen)].set_index("pays")
    accommodation_chart = accommodation_view[
        ["part_hotels_pct", "part_locations_courte_duree_pct", "part_campings_pct"]
    ].rename(columns={
        "part_hotels_pct": "Hôtels",
        "part_locations_courte_duree_pct": "Locations courte durée",
        "part_campings_pct": "Campings",
    })
    st.bar_chart(accommodation_chart)

with tab_budget:
    st.subheader("Tarifs indicatifs en euros · France, Espagne et Italie")
    st.caption(
        "Lecture prioritaire : prix unitaires estimés à partir d'une base française modifiable. "
        "Ils donnent des ordres de grandeur comparables, pas des prix de réservation en temps réel."
    )

    country_colors = alt.Scale(
        domain=["Espagne", "Italie", "France"],
        range=["#f2b134", "#2a9d8f", "#457b9d"],
    )
    price_lookup = detailed_prices_df.set_index(["geo", "code_eurostat"])["indice_prix"].to_dict()
    reference_rows = []
    for _, row in budget_df.iterrows():
        french_index = price_lookup.get(("FR", row["code_proxy"]))
        for geo, country in [("ES", "Espagne"), ("IT", "Italie"), ("FR", "France")]:
            country_index = price_lookup.get((geo, row["code_proxy"]))
            ratio = country_index / french_index if french_index and country_index else 1.0
            reference_rows.append({
                "poste": row["poste"],
                "unite": row["unite"],
                "pays": country,
                "prix_unitaire_estime": float(row["prix_base_france_eur"]) * ratio,
                "quantite": float(row["quantite_defaut"]),
            })
    reference_prices = pd.DataFrame(reference_rows)
    reference_prices["budget_poste"] = (
        reference_prices["prix_unitaire_estime"] * reference_prices["quantite"]
    )
    reference_totals = reference_prices.groupby("pays")["budget_poste"].sum().to_dict()

    e1, e2, e3 = st.columns(3)
    e1.metric(
        "Séjour de référence · Espagne",
        f"{reference_totals.get('Espagne', 0):,.0f} €".replace(",", " "),
        f"{reference_totals.get('Espagne', 0) - reference_totals.get('France', 0):+,.0f} € vs France".replace(",", " "),
        delta_color="inverse",
    )
    e2.metric(
        "Séjour de référence · Italie",
        f"{reference_totals.get('Italie', 0):,.0f} €".replace(",", " "),
        f"{reference_totals.get('Italie', 0) - reference_totals.get('France', 0):+,.0f} € vs France".replace(",", " "),
        delta_color="inverse",
    )
    e3.metric("Séjour de référence · France", f"{reference_totals.get('France', 0):,.0f} €".replace(",", " "))

    euro_bars = alt.Chart(reference_prices).mark_bar(
        cornerRadiusTopLeft=3, cornerRadiusTopRight=3
    ).encode(
        x=alt.X("poste:N", title=None, axis=alt.Axis(labelAngle=-25, labelLimit=180)),
        xOffset=alt.XOffset("pays:N", sort=["Espagne", "Italie", "France"]),
        y=alt.Y("prix_unitaire_estime:Q", title="Prix unitaire indicatif (€)"),
        color=alt.Color("pays:N", title="Pays", scale=country_colors),
        tooltip=[
            alt.Tooltip("poste:N", title="Poste"),
            alt.Tooltip("pays:N", title="Pays"),
            alt.Tooltip("unite:N", title="Unité"),
            alt.Tooltip("prix_unitaire_estime:Q", title="Prix indicatif", format=".2f"),
        ],
    )
    euro_labels = euro_bars.mark_text(dy=-8, fontSize=12).encode(
        text=alt.Text("prix_unitaire_estime:Q", format=".0f"),
        color=alt.value("#888"),
    )
    st.altair_chart((euro_bars + euro_labels).properties(height=430), use_container_width=True)

    euro_table = reference_prices.pivot(
        index=["poste", "unite"], columns="pays", values="prix_unitaire_estime"
    ).reset_index()
    st.dataframe(
        euro_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "poste": "Poste",
            "unite": "Unité",
            "Espagne": st.column_config.NumberColumn("Espagne", format="%.2f €"),
            "Italie": st.column_config.NumberColumn("Italie", format="%.2f €"),
            "France": st.column_config.NumberColumn("France", format="%.2f €"),
        },
    )
    st.info(
        "Scénario par défaut : 3 nuits, 4 déjeuners, 4 dîners, 4 boissons alcoolisées, "
        "4 boissons sans alcool, 3 jours de transport local et 2 activités."
    )

    st.divider()
    st.subheader("Indices officiels utilisés pour calculer les écarts")
    st.caption(
        f"Indices Eurostat {year}, moyenne UE = 100. Un indice de 85 signifie un niveau de prix "
        "environ 15 % inférieur à la moyenne européenne ; ce n'est pas un tarif en euros."
    )

    category_order = list(dict.fromkeys(detailed_prices_df["categorie"].tolist()))
    selected_price_categories = st.multiselect(
        "Catégories affichées",
        category_order,
        default=category_order,
        key="detailed_price_categories",
    )
    price_view = detailed_prices_df[
        detailed_prices_df["categorie"].isin(selected_price_categories)
    ].copy()

    if price_view.empty:
        st.info("Sélectionnez au moins une catégorie.")
    else:
        bars = alt.Chart(price_view).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X(
                "categorie:N",
                sort=selected_price_categories,
                title=None,
                axis=alt.Axis(labelAngle=-25, labelLimit=180),
            ),
            xOffset=alt.XOffset("pays:N", sort=["Espagne", "Italie", "France"]),
            y=alt.Y("indice_prix:Q", title="Indice de prix · UE=100", scale=alt.Scale(zero=False)),
            color=alt.Color("pays:N", title="Pays", scale=country_colors),
            tooltip=[
                alt.Tooltip("pays:N", title="Pays"),
                alt.Tooltip("categorie:N", title="Catégorie"),
                alt.Tooltip("indice_prix:Q", title="Indice UE=100", format=".1f"),
                alt.Tooltip("limite:N", title="Précision"),
            ],
        )
        labels = bars.mark_text(dy=-8, fontSize=12).encode(
            text=alt.Text("indice_prix:Q", format=".1f"),
            color=alt.value("#777"),
        )
        reference = alt.Chart(pd.DataFrame({"niveau": [100]})).mark_rule(
            color="#888", strokeDash=[5, 4]
        ).encode(y="niveau:Q")
        st.altair_chart((bars + labels + reference).properties(height=430), use_container_width=True)

        st.dataframe(
            price_view.pivot(index="categorie", columns="pays", values="indice_prix")
            .reindex(selected_price_categories)
            .reset_index(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "categorie": "Catégorie officielle",
                "Espagne": st.column_config.NumberColumn("Espagne", format="%.1f"),
                "Italie": st.column_config.NumberColumn("Italie", format="%.1f"),
                "France": st.column_config.NumberColumn("France", format="%.1f"),
            },
        )

    st.divider()
    st.subheader("Personnaliser les prix et le budget")
    st.warning(
        "Les montants ci-dessous ne sont pas des tarifs moyens observés. Vous saisissez une base française, "
        "puis l'application estime les équivalents espagnol et italien à partir des indices officiels. "
        "Pour les bars, le proxy est le prix de détail des boissons : la marge du débitant n'est pas mesurée."
    )

    budget_editor = budget_df[[
        "poste", "unite", "quantite_defaut", "prix_base_france_eur", "code_proxy", "precision"
    ]].rename(columns={"quantite_defaut": "quantite"})
    edited_budget = st.data_editor(
        budget_editor,
        use_container_width=True,
        hide_index=True,
        disabled=["poste", "unite", "code_proxy", "precision"],
        column_config={
            "poste": "Poste",
            "unite": "Unité",
            "quantite": st.column_config.NumberColumn("Quantité", min_value=0.0, step=1.0, format="%.0f"),
            "prix_base_france_eur": st.column_config.NumberColumn("Prix unitaire France (€)", min_value=0.0, step=1.0, format="%.2f €"),
            "code_proxy": None,
            "precision": "Précision méthodologique",
        },
        key="budget_editor",
    )

    budget_rows = []
    for _, row in edited_budget.iterrows():
        french_index = price_lookup.get(("FR", row["code_proxy"]))
        for geo, country in [("ES", "Espagne"), ("IT", "Italie"), ("FR", "France")]:
            country_index = price_lookup.get((geo, row["code_proxy"]))
            ratio = country_index / french_index if french_index and country_index else 1.0
            unit_price = float(row["prix_base_france_eur"]) * ratio
            budget_rows.append({
                "poste": row["poste"],
                "pays": country,
                "prix_unitaire_estime": unit_price,
                "quantite": float(row["quantite"]),
                "budget_estime": unit_price * float(row["quantite"]),
            })
    budget_result = pd.DataFrame(budget_rows)

    totals = budget_result.groupby("pays", as_index=False)["budget_estime"].sum()
    total_map = totals.set_index("pays")["budget_estime"].to_dict()
    b1, b2, b3 = st.columns(3)
    b1.metric(
        "Budget Espagne",
        f"{total_map.get('Espagne', 0):,.0f} €".replace(",", " "),
        f"{total_map.get('Espagne', 0) - total_map.get('France', 0):+,.0f} € vs France".replace(",", " "),
        delta_color="inverse",
    )
    b2.metric(
        "Budget Italie",
        f"{total_map.get('Italie', 0):,.0f} €".replace(",", " "),
        f"{total_map.get('Italie', 0) - total_map.get('France', 0):+,.0f} € vs France".replace(",", " "),
        delta_color="inverse",
    )
    b3.metric("Budget France saisi", f"{total_map.get('France', 0):,.0f} €".replace(",", " "))

    budget_bars = alt.Chart(budget_result).mark_bar(
        cornerRadiusTopLeft=3, cornerRadiusTopRight=3
    ).encode(
        x=alt.X("poste:N", title=None, axis=alt.Axis(labelAngle=-25, labelLimit=170)),
        xOffset=alt.XOffset("pays:N", sort=["Espagne", "Italie", "France"]),
        y=alt.Y("budget_estime:Q", title="Budget estimé (€)"),
        color=alt.Color("pays:N", title="Pays", scale=country_colors),
        tooltip=[
            alt.Tooltip("poste:N", title="Poste"),
            alt.Tooltip("pays:N", title="Pays"),
            alt.Tooltip("prix_unitaire_estime:Q", title="Prix unitaire estimé", format=".2f"),
            alt.Tooltip("quantite:Q", title="Quantité", format=".0f"),
            alt.Tooltip("budget_estime:Q", title="Budget estimé", format=".2f"),
        ],
    )
    budget_labels = budget_bars.mark_text(dy=-8, fontSize=11).encode(
        text=alt.Text("budget_estime:Q", format=".0f"),
        color=alt.value("#777"),
    )
    st.altair_chart((budget_bars + budget_labels).properties(height=420), use_container_width=True)

    with st.expander("Voir le détail calculé"):
        st.dataframe(
            budget_result,
            use_container_width=True,
            hide_index=True,
            column_config={
                "poste": "Poste",
                "pays": "Pays",
                "prix_unitaire_estime": st.column_config.NumberColumn("Prix unitaire estimé", format="%.2f €"),
                "quantite": st.column_config.NumberColumn("Quantité", format="%.0f"),
                "budget_estime": st.column_config.NumberColumn("Budget estimé", format="%.2f €"),
            },
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
        "Les indices de prix comparent les niveaux entre pays, avec une moyenne UE égale à 100. "
        "Eurostat ne sépare pas hôtels et restaurants. Pour les bars, les boissons achetées au détail servent "
        "uniquement de proxy : aucun prix harmonisé au comptoir n'est disponible. Le simulateur en euros applique "
        "ces écarts relatifs aux hypothèses françaises saisies par l'utilisateur."
    )
    st.dataframe(
        sources_df,
        use_container_width=True,
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("Lien direct")},
    )
    st.caption(f"Dernière extraction : {metadata.get('date_actualisation_utc', 'N/D')}")
