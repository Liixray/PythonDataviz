# filename = 'dash-01.py'

#
# Imports
#
import plotly_express as px
import plotly.graph_objects as go
import pandas as pds
import dash
from dash import dcc
from dash import html
import dash_daq as daq
import json
from typing import Any
from src.utils import  draw_graph,format_graph_data, get_data, clean_data


#  iris.rename(columns={   "sepal.length": "sepal_length",
#                     "sepal.width": "sepal_width",
#                     "petal.length": "petal_length",
#                     "petal.width": "petal_width"},
#                         inplace = True)
get_data.downloadDataset()
clean_data.cleanDataset()

with open("data/cleaned/countries.geo.json", "r") as f:
    countries = json.load(f)

# Default values
year = 2020
country_name = "France"
displayPrimaryOnMap = True

worldEducation = pds.read_csv("data/cleaned/cleaned-world-education-data.csv")

correlationData = format_graph_data.getCorrelationData(worldEducation)
continentEducationData = format_graph_data.getContinentEducationData(worldEducation, year)
worldEducationForMap, maxPupilTeacher = format_graph_data.getMapData(
    worldEducation, year, displayPrimaryOnMap
)
bubbleData = format_graph_data.getBubbleData(worldEducation, year)
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

    bubbleData = format_graph_data.getBubbleData(worldEducation, year)
    worldEducationForMap, maxPupilTeacher = format_graph_data.getMapData(
        worldEducation, year, displayPrimaryOnMap
    )
    continentEducationData = format_graph_data.getContinentEducationData(worldEducation, year)
    return [
        draw_graph.drawEducationWorldMap(
            worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
        ),
        draw_graph.drawBubbleGraph(bubbleData),
        draw_graph.drawContinentGDPGraph(continentEducationData),
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
    worldEducationForMap, maxPupilTeacher = format_graph_data.getMapData(
        worldEducation, year, displayPrimaryOnMap
    )
    return draw_graph.drawEducationWorldMap(
        worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
    )


@app.callback(
    dash.Output(component_id="heatmap", component_property="figure"),
    dash.Input(component_id="heatmap-switch", component_property="on"),
)
def ToggleHeatMapText(on: bool) -> go.Figure:
    return px.imshow(correlationData, text_auto=on,labels={"color": "Corrélation"})


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
        draw_graph.drawCountryCurveEvolution(countryEducationData),
        draw_graph.drawCountryPIBLiteratePopulation(countryEducationData),
    ]


# endregion

if __name__ == "__main__":
    bubbleGraph = draw_graph.drawBubbleGraph(bubbleData)
    heatmap = px.imshow(correlationData, text_auto=False,labels={"color": "Corrélation"})
    educationWorldMap = draw_graph.drawEducationWorldMap(
        worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher
    )
    continentGDPGraph = draw_graph.drawContinentGDPGraph(continentEducationData)

    countryCurveEvolution = draw_graph.drawCountryCurveEvolution(countryEducationData)
    countryPIBLiteratePopulation = draw_graph.drawCountryPIBLiteratePopulation(
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
                                    La carte ci-dessous montre le nombre moyen d'élèves par professeurs dans les différentes pays. Pour les pays n'ayant pas de données en {year}, nous prenons les données les plus récentes en {year}.
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
                ],
                className="graphs-cont",
            ),
            
            html.Div(
                children=[
                    html.H2(children="Graphiques du pays : NomDuPays", className="graph-cont-title"),
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
                    )
                ],
                className="graphs-cont"
            )
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
