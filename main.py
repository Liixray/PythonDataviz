# filename = 'dash-01.py'

#
# Imports
#
import numpy as np
import plotly_express as px
import plotly.graph_objects as go
import pandas as pds
import dash
from dash import dcc
from dash import html
import dash_daq as daq
import json
import kaggle
from typing import Any

continent_colors = {
    "Africa": "#5bb73b",
    "Asia": "#ffeb28",
    "Europe": "#4330e1",
    "North America": "#ed431f",
    "Oceania": "#8b26b7",
    "South America": "#f99f2c",
}


def downloadAndCleanDataset() -> None:
    # Download the raw dataset
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        "bushraqurban/world-education-dataset", path="data/raw", unzip=True
    )

    # Add continent informations to the default dataset
    rawCountryContinentData = pds.read_csv(
        "data/raw/country-and-continent-codes-list.csv"
    )
    rawWorldEducationData = pds.read_csv("data/raw/world-education-data.csv")
    cleanWorldEducationData = pds.merge(
        rawWorldEducationData,
        rawCountryContinentData[["Continent_Name", "Three_Letter_Country_Code"]],
        left_on="country_code",
        right_on="Three_Letter_Country_Code",
    )
    cleanWorldEducationData.to_csv("data/cleaned/cleaned-world-education-data.csv")


# region Data formatting functions


def getMapData(
    baseData: pds.DataFrame, year: int, displayPrimary: bool
) -> tuple[pds.DataFrame, int]:
    columnName = (
        "pupil_teacher_primary" if displayPrimary else "pupil_teacher_secondary"
    )
    worldEducationForMap = baseData[
        (baseData[columnName].notna()) & (baseData["year"] <= year)
    ]
    worldEducationForMap = worldEducationForMap.sort_values(
        by=["country", "year"], ascending=[True, False]
    )
    worldEducationForMap = worldEducationForMap.drop_duplicates(
        subset="country", keep="first"
    )
    maxPupilTeacher = worldEducationForMap[columnName].max()
    return worldEducationForMap, maxPupilTeacher


def getContinentEducationData(baseData: pds.DataFrame, year: int) -> pds.DataFrame:
    continentEducationData = baseData[
        (baseData["gov_exp_pct_gdp"].notna()) & (baseData["year"] <= year)
    ]
    continentEducationData = continentEducationData.sort_values(
        by=["country", "year"], ascending=[True, False]
    )
    continentEducationData = continentEducationData.drop_duplicates(
        subset="country", keep="first"
    )
    return (
        continentEducationData.groupby("Continent_Name")["gov_exp_pct_gdp"]
        .mean()
        .reset_index()
    )


def getBubbleData(baseData: pds.DataFrame, year: int) -> pds.DataFrame:
    bubbleData = baseData[baseData["year"] == year]
    bubbleData.loc[:, "gov_exp_pct_gdp"] = (
        bubbleData["gov_exp_pct_gdp"].fillna(0).astype(float)
    )
    return bubbleData


def getCorrelationData(baseData: pds.DataFrame) -> pds.DataFrame:
    dataTypes = baseData.select_dtypes(include=[np.number])
    correlationData = dataTypes.corr().round(2)
    return correlationData


# endregion


# region drawing graphs
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
                if displayPrimaryOnMap
                else "pupil_teacher_secondary"
            ): "Nombre d'élèves par professeurs"
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
        color=bubbleData["Continent_Name"],
        color_discrete_map=continent_colors,
    )


def drawContinentGDPGraph(continentEducationData: pds.DataFrame) -> go.Figure:
    global continent_colors
    return px.histogram(
        continentEducationData,
        x="Continent_Name",
        y="gov_exp_pct_gdp",
        color=continentEducationData["Continent_Name"],
        color_discrete_map=continent_colors,
    )


def drawCountryCurveEvolution(countryEducationData: pds.DataFrame) -> go.Figure:
    yAxisColumns = [
        "school_enrol_primary_pct",
        "school_enrol_secondary_pct",
        "school_enrol_tertiary_pct",
        "lit_rate_adult_pct",
    ]
    countryCurveEvolution = px.line(
        countryEducationData,
        x="year",
        y=yAxisColumns,
        range_y=[0, max(105, countryEducationData[yAxisColumns].max().max() + 5)],
    )
    countryCurveEvolution.update_traces(connectgaps=True)
    return countryCurveEvolution


def drawCountryPIBLiteratePopulation(countryGraphData: pds.DataFrame) -> go.Figure:
    countryPIBLiteratePopulation = go.Figure()

    # Ajouter la première série de données (Valeur_1)
    countryPIBLiteratePopulation.add_trace(
        go.Bar(
            x=countryGraphData["year"],
            y=countryGraphData["gov_exp_pct_gdp"],
            name="Pourcentage du PB investi dans l'éducation",  # Nom affiché dans la légende
            marker_color="blue",  # Couleur des barres
        )
    )

    # Ajouter la deuxième série de données (Valeur_2)
    countryPIBLiteratePopulation.add_trace(
        go.Bar(
            x=countryGraphData["year"],
            y=countryGraphData["lit_rate_adult_pct"],
            name="Pourcentage de la population lettrée",  # Nom affiché dans la légende
            marker_color="orange",  # Couleur des barres
        )
    )

    # Mettre les barres côte à côte
    countryPIBLiteratePopulation.update_layout(
        barmode="group",  # Les barres sont côte à côte
        title="Comparaison des Valeurs 1 et 2 par Année",
        xaxis=dict(
            title="Année",
            tickmode="linear",  # Mode linéaire
            dtick=1,  # Afficher les ticks tous les 5 ans
        ),
        yaxis_title="Valeur",
        legend_title="Type de Valeur",
        yaxis_range=[0, 105],
    )

    return countryPIBLiteratePopulation


# endregion


#  iris.rename(columns={   "sepal.length": "sepal_length",
#                     "sepal.width": "sepal_width",
#                     "petal.length": "petal_length",
#                     "petal.width": "petal_width"},
#                         inplace = True)
downloadAndCleanDataset()

with open("data/cleaned/countries.geo.json", "r") as f:
    countries = json.load(f)

# Default values
year = 2020
country_name = "France"
displayPrimaryOnMap = True

worldEducation = pds.read_csv("data/cleaned/cleaned-world-education-data.csv")

correlationData = getCorrelationData(worldEducation)
continentEducationData = getContinentEducationData(worldEducation, year)
worldEducationForMap, maxPupilTeacher = getMapData(
    worldEducation, year, displayPrimaryOnMap
)
bubbleData = getBubbleData(worldEducation, year)
countryEducationData = worldEducation[worldEducation["country"] == country_name]


app = dash.Dash(__name__)


# region callaback functions
@app.callback(
    [
        dash.Output(component_id="educationWorldMap", component_property="figure"),
        dash.Output(component_id="bubbleGraph", component_property="figure"),
        dash.Output(component_id="continentGDPGraph", component_property="figure"),
    ],
    [dash.Input(component_id="year-slider", component_property="value")],
)
def updateYear(input_value: int) -> list[go.Figure]:
    global displayPrimaryOnMap, worldEducationForMap, maxPupilTeacher, bubbleData, continentEducationData, year

    year = input_value

    bubbleData = getBubbleData(worldEducation, year)
    worldEducationForMap, maxPupilTeacher = getMapData(
        worldEducation, year, displayPrimaryOnMap
    )
    continentEducationData = getContinentEducationData(worldEducation, year)
    return [
        drawEducationWorldMap(
            worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
        ),
        drawBubbleGraph(bubbleData),
        drawContinentGDPGraph(continentEducationData),
    ]


@app.callback(
    dash.Output(
        component_id="educationWorldMap",
        component_property="figure",
        allow_duplicate=True,
    ),
    [
        dash.Input(component_id="map-button-elementary", component_property="n_clicks"),
        dash.Input(component_id="map-button-secondary", component_property="n_clicks"),
    ],
    prevent_initial_call=True,
)
def changeMapSchoolType(elementary_button: str, secondary_button: str) -> go.Figure:
    global displayPrimaryOnMap, worldEducationForMap, year
    if "map-button-elementary" == dash.ctx.triggered_id:
        displayPrimaryOnMap = True
    elif "map-button-secondary" == dash.ctx.triggered_id:
        displayPrimaryOnMap = False
    worldEducationForMap, maxPupilTeacher = getMapData(
        worldEducation, year, displayPrimaryOnMap
    )
    return drawEducationWorldMap(
        worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
    )


@app.callback(
    dash.Output(component_id="heatmap", component_property="figure"),
    dash.Input(component_id="heatmap-switch", component_property="on"),
)
def ToggleHeatMapText(on: bool) -> go.Figure:
    return px.imshow(correlationData, text_auto=on)


# Now create the graph that updates the country name based on hover and showing Years on x-axis and Display value
# of chosen dataframe on y-axis
@app.callback(
    [
        dash.Output(component_id="countryCurveEvolution", component_property="figure"),
        dash.Output(
            component_id="countryPIBLiteratePopulation", component_property="figure"
        ),
    ],
    dash.Input(component_id="educationWorldMap", component_property="clickData"),
)
def updateCountryBasedGraph(clickData: dict[str, Any]) -> list[go.Figure]:
    global country_name, countryEducationData
    if clickData is not None:
        country_name = clickData["points"][0]["hovertext"]
        countryEducationData = worldEducation[worldEducation["country"] == country_name]

    return [
        drawCountryCurveEvolution(countryEducationData),
        drawCountryPIBLiteratePopulation(countryEducationData),
    ]


# endregion

if __name__ == "__main__":
    bubbleGraph = drawBubbleGraph(bubbleData)
    heatmap = px.imshow(correlationData, text_auto=False)
    educationWorldMap = drawEducationWorldMap(
        worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
    )
    continentGDPGraph = drawContinentGDPGraph(continentEducationData)

    countryCurveEvolution = drawCountryCurveEvolution(countryEducationData)
    countryPIBLiteratePopulation = drawCountryPIBLiteratePopulation(
        countryEducationData
    )

    app.layout = html.Div(
        children=[
            ######### Titre de la page #########
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H1(children="World Education DashBoard"),
                            html.H2(children="Idrissi Nidal - Leveque Lucas"),
                        ],
                        className="titles",
                    ),
                ],
                className="hero",
            ),
            ####################################
            ################ Les deux premiers graphiques  ################
            # Row avec les deux premiers graphiques
            html.Div(
                children=[
                    # Column pour la heatmap et le switch
                    html.Div(
                        children=[
                            dcc.Loading(
                                [
                                    dcc.Graph(id="heatmap", figure=heatmap),
                                    daq.BooleanSwitch(
                                        id="heatmap-switch",
                                        on=False,
                                        label="Afficher les valeurs",
                                    ),
                                ],
                                type="default",
                                overlay_style={
                                    "visibility": "visible",
                                    "opacity": 0.5,
                                    "backgroundColor": "white",
                                },
                            )
                        ],
                        className="column",
                    ),
                    # Histogramme
                    dcc.Loading(
                        dcc.Graph(id="continentGDPGraph", figure=continentGDPGraph),
                        type="default",
                        overlay_style={
                            "visibility": "visible",
                            "opacity": 0.5,
                            "backgroundColor": "white",
                        },
                    ),
                ],
                className="row",
            ),
            ################################################################
            ################## Graphs avec dates #####################
            html.Div(
                children=[
                    html.H3(children="Select a year", className="slider-title"),
                    html.Div(
                        children=[
                            dcc.Slider(
                                id="year-slider",
                                min=1999,
                                max=2020,
                                step=1,
                                marks={year: str(year) for year in range(1999, 2021)},
                                value=year,  # Année sélectionnée par défaut
                            ),
                        ],
                        className="slider-bg",
                    ),
                    html.Div(
                        children=[
                            html.H3(
                                children="Ceci est un titre", className="section-title"
                            ),
                            dcc.Loading(
                                dcc.Graph(id="bubbleGraph", figure=bubbleGraph),
                                type="default",
                                overlay_style={
                                    "visibility": "visible",
                                    "opacity": 0.5,
                                    "backgroundColor": "white",
                                },
                            ),
                        ],
                        className="paragraph",
                    ),
                    html.Div(
                        children=[
                            html.H3(
                                children="Ceci est un titre", className="section-title"
                            ),
                            html.Div(
                                children=f"""
                                    La carte ci-desosus montre le nombre moyen d'élèves par professeurs dans les différentes pays. Pour les pays n'ayant pas dedonnées en {year}, nous prenons les données les plus récentes en {year}.
                                """
                            ),  
                            html.Div(
                                children=[
                                    html.Button(
                                        id="map-button-elementary",
                                        children="Élémentaire",
                                        className="button",
                                    ),
                                    html.Button(
                                        id="map-button-secondary",
                                        children="Secondaire",
                                        className="button",
                                    ),
                                ],
                                className="buttons",
                            ),
                            dcc.Loading(
                                dcc.Graph(
                                    id="educationWorldMap",
                                    figure=educationWorldMap,
                                ),  
                                type="default",
                                overlay_style={
                                    "visibility": "visible",
                                    "opacity": 0.5,
                                    "backgroundColor": "white",
                                },
                            ),
                        ],
                        className="paragraph",
                    ),
                    html.Div(
                        children=[
                            html.H3(
                                children="Ceci est un titre", className="section-title"
                            ),
                            dcc.Loading(
                                dcc.Graph(
                                    id="countryCurveEvolution",
                                    figure=countryCurveEvolution,
                                ),
                                type="default",
                                overlay_style={
                                    "visibility": "visible",
                                    "opacity": 0.5,
                                    "backgroundColor": "white",
                                },
                            ),
                        ],
                        className="paragraph",
                    ),
                    html.Div(
                        children=[
                            html.H3(
                                children="Ceci est un titre", className="section-title"
                            ),
                            dcc.Loading(
                                dcc.Graph(
                                    id="countryPIBLiteratePopulation",
                                    figure=countryPIBLiteratePopulation,
                                ),
                                type="default",
                                overlay_style={
                                    "visibility": "visible",
                                    "opacity": 0.5,
                                    "backgroundColor": "white",
                                },
                            ),
                        ],
                        className="paragraph",
                    ),
                ],
                className="year-graphs-cont",
            ),
            # html.H1(children=f'Heatmap de la corrélation entre les données du dataset',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.Div(children=f'''
            #     On peut voir que .... TODO .
            # '''), 
            # html.H1(children=f'Histogramme : ',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.Div(children=f'''
            #     On peut voir que .... TODO .
            # '''), 
            # html.H1(children=f'Ratio d\élèves par professeur en '+'élémentaire 'if displayPrimaryOnMap else 'secondaire'+' en ({year})',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.H1(children=f'Bubble graph des statistiques des écoles primaires par continent',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.Div(children=f'''
            #     On peut voir que .... TODO .
            # '''), 
            # html.H1(children=f'Données concernant: '+country_name,
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.H1(children=f'Courbe',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.Div(children=f'''
            #     On peut voir que .... TODO .
            # '''), 
            # html.H1(children=f'Histogramme',
            #             style={'textAlign': 'center', 'color': '#7FDBFF'}), 
            # html.Div(children=f'''
            #     On peut voir que .... TODO .
            # '''), 
        ],
        className="cont",
    )

    #
    # RUN APP
    #

    app.run_server(debug=True)
