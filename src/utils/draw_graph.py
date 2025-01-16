import plotly_express as px
import plotly.graph_objects as go
import pandas as pds
from typing import Any

continent_colors = {
    "Africa": "#5bb73b",
    "Asia": "#ffeb28",
    "Europe": "#4330e1",
    "North America": "#ed431f",
    "Oceania": "#8b26b7",
    "South America": "#f99f2c",
}


def drawEducationWorldMap(
    worldEducationMapData: pds.DataFrame,
    countries: dict[str, Any],
    shouldDisplayPrimary: bool,
    maxPupilTeacher: int,
) -> go.Figure:
    return px.choropleth_map(
        worldEducationMapData,
        geojson=countries,
        locations="country_code",
        color=(
            "pupil_teacher_primary"
            if shouldDisplayPrimary
            else "pupil_teacher_secondary"
        ),
        color_continuous_scale="YlGnBu",
        range_color=(0, maxPupilTeacher),
        map_style="carto-positron",
        zoom=1,
        center={"lat": 37.0902, "lon": -95.7129},
        opacity=0.5,
        hover_data="country_code",
        hover_name="country",
        labels={
            (
                "pupil_teacher_primary"
                if shouldDisplayPrimary
                else "pupil_teacher_secondary"
            ): "Nombre d'élèves par professeurs",
            "country_code": "Code du pays",
        },
    )


def drawBubbleGraph(bubbleGraphData: pds.DataFrame) -> go.Figure:
    global continent_colors
    return px.scatter(
        bubbleGraphData,
        x="school_enrol_primary_pct",
        y="pri_comp_rate_pct",
        size="gov_exp_pct_gdp",
        hover_name="country",
        color=bubbleGraphData["Continent_Name"],
        color_discrete_map=continent_colors,
        labels={
            "school_enrol_primary_pct": "Taux de scolarisation primaire en pourcentage",
            "pri_comp_rate_pct": "Taux de réussite du cycle primaire en pourcentage",
            "gov_exp_pct_gdp": "Pourcentage du PIB investi dans l'éducation",
            "Continent_Name": "Continent",
        },
    )


def drawContinentGDPGraph(continentEducationData: pds.DataFrame) -> go.Figure:
    global continent_colors
    return px.histogram(
        continentEducationData,
        x="Continent_Name",
        y="gov_exp_pct_gdp",
        color=continentEducationData["Continent_Name"],
        color_discrete_map=continent_colors,
        labels={
            "gov_exp_pct_gdp": "Pourcentage du PIB investi dans l'éducation",
            "Continent_Name": "Continent",
        },
    ).update_layout(yaxis_title="Pourcentage moyen du PIB investi dans l'éducation").update_traces(hovertemplate='Continent: %{x} <br>PIB investi dans l\'éducation: %{y}%')


def drawCountryCurveEvolution(countryEducationData: pds.DataFrame) -> go.Figure:
    yAxisColumns = [
        "school_enrol_primary_pct",
        "school_enrol_secondary_pct",
        "school_enrol_tertiary_pct",
        "lit_rate_adult_pct",
    ]
    newnames = {
        "school_enrol_primary_pct": "Taux de scolarisation primaire en pourcentage",
        "school_enrol_secondary_pct": "Taux de scolarisation secondaire en pourcentage",
        "school_enrol_tertiary_pct": "Taux de scolarisation tertiaire en pourcentage",
        "lit_rate_adult_pct": "Taux d'alphabétisation des adultes en pourcentage",
    }

    countryCurveEvolution = px.line(
        countryEducationData,
        x="year",
        y=yAxisColumns,
        range_y=[0, max(105, countryEducationData[yAxisColumns].max().max() + 5)],
        labels={"year": "Année", "value": "Pourcentage", "variable":"Légende"},
    )
    countryCurveEvolution.update_traces(connectgaps=True)
    countryCurveEvolution.for_each_trace(lambda t: t.update(name=newnames[t.name]))
    return countryCurveEvolution


def drawCountryPIBLiteratePopulation(countryGraphData: pds.DataFrame) -> go.Figure:
    countryPIBLiteratePopulation = go.Figure()

    countryPIBLiteratePopulation.add_trace(
        go.Bar(
            x=countryGraphData["year"],
            y=countryGraphData["gov_exp_pct_gdp"],
            name="Pourcentage du PB investi dans l'éducation",
            marker_color="blue",
        )
    )

    countryPIBLiteratePopulation.add_trace(
        go.Bar(
            x=countryGraphData["year"],
            y=countryGraphData["lit_rate_adult_pct"],
            name="Pourcentage de la population lettrée",  #
            marker_color="orange",
        )
    )

    countryPIBLiteratePopulation.update_layout(
        barmode="group",
        xaxis=dict(
            title="Année",
            tickmode="linear",
            dtick=1,
        ),
        yaxis_title="Pourcentage",
        yaxis_range=[0, 105],
    )

    return countryPIBLiteratePopulation
