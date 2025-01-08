# filename = 'dash-01.py'

#
# Imports
#
import numpy as np
import plotly_express as px
import plotly.graph_objects as go
import pandas as pds
import math
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import json
import kaggle

continent_colors = {"Africa":'#5bb73b',
                            "Asia":"#ffeb28",
                            "Europe":"#4330e1",
                            "North America":'#ed431f',
                            "Oceania":"#8b26b7",
                            "South America":"#f99f2c"}


def downloadAndCleanDataset():
    # Download the raw dataset
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files('bushraqurban/world-education-dataset', path='data/raw', unzip=True)

    # Add continent informations to the default dataset
    rawCountryContinentData = pds.read_csv("data/raw/country-and-continent-codes-list.csv")
    rawWorldEducationData = pds.read_csv("data/raw/world-education-data.csv")
    cleanWorldEducationData = pds.merge(rawWorldEducationData, rawCountryContinentData[["Continent_Name","Three_Letter_Country_Code"]], left_on="country_code", right_on="Three_Letter_Country_Code")
    cleanWorldEducationData.to_csv("data/clean/cleaned-world-education-data.csv")

#region Data formatting functions 
    
def getMapData(baseData,year,displayPrimary):
    columnName= "pupil_teacher_primary" if displayPrimary else "pupil_teacher_secondary"
    worldEducationForMap = baseData[(baseData[columnName].notna())&(baseData["year"]<=year)]
    worldEducationForMap = worldEducationForMap.sort_values(by=['country','year'],ascending=[True,False])
    worldEducationForMap = worldEducationForMap.drop_duplicates(subset="country",keep="first")
    maxPupilTeacher = worldEducationForMap[columnName].max()
    return worldEducationForMap, maxPupilTeacher

def getContinentEducationData(baseData,year):
    continentEducationData = baseData[(baseData['gov_exp_pct_gdp'].notna())&(baseData["year"]<=year)]
    continentEducationData = continentEducationData.sort_values(by=['country','year'],ascending=[True,False])
    continentEducationData = continentEducationData.drop_duplicates(subset="country",keep="first")
    return continentEducationData.groupby('Continent_Name')['gov_exp_pct_gdp'].mean().reset_index()
    
def getBubbleData(baseData, year):
    bubbleData = baseData[baseData["year"]==year ]
    bubbleData['gov_exp_pct_gdp'] = bubbleData['gov_exp_pct_gdp'].fillna(0).astype(float)
    return bubbleData

def getCorrelationData(baseData):
    dataTypes = baseData.select_dtypes(include=[np.number])
    correlationData = dataTypes.corr().round(2)
    return correlationData

#endregion

#region drawing graphs
def drawEducationWorldMap(worldEducationMapData, countries, shouldDisplayPrimary, maxPupilTeacher):
    return px.choropleth_map(worldEducationMapData, geojson=countries, locations='country_code', 
                                  color='pupil_teacher_primary' if shouldDisplayPrimary else 'pupil_teacher_secondary',
                                    color_continuous_scale="YlGnBu",
                                    range_color=(0, maxPupilTeacher),
                                    map_style="carto-positron",
                                    zoom=1, center = {"lat": 37.0902, "lon": -95.7129},
                                    opacity=0.5,
                           hover_data="country_code",
                           hover_name="country",
                           labels={'pupil_teacher_primary' if displayPrimaryOnMap else 'pupil_teacher_secondary':'Nombre d\'élèves par professeurs'}
                                    )
    
def drawBubbleGraph(bubbleGraphData):
    global continent_colors
    return px.scatter(
                bubbleGraphData,
                x="school_enrol_primary_pct",
                y="pri_comp_rate_pct",
                size="gov_exp_pct_gdp",
                hover_name="country",
                color=bubbleData["Continent_Name"],
                color_discrete_map=continent_colors
                )

def drawContinentGDPGraph(continentEducationData):
    global continent_colors
    return px.histogram(continentEducationData,x="Continent_Name",y="gov_exp_pct_gdp",color=continentEducationData["Continent_Name"],color_discrete_map=continent_colors)

def drawCountryCurveEvolution(countryEducationData):
    yAxisColumns = ["school_enrol_primary_pct","school_enrol_secondary_pct","school_enrol_tertiary_pct","lit_rate_adult_pct"]
    countryCurveEvolution = px.line(
        countryEducationData,
        x="year",y=yAxisColumns,
        range_y=[0,max(105,countryEducationData[yAxisColumns].max().max()+5)])
    countryCurveEvolution.update_traces(connectgaps=True)
    return countryCurveEvolution

def drawCountryGraph2(countryGraphData):
    graphCountry2 = go.Figure()

    # Ajouter la première série de données (Valeur_1)
    graphCountry2.add_trace(go.Bar(
        x=countryGraphData['year'],
        y=countryGraphData['gov_exp_pct_gdp'],
        name='Pourcentage du PB investi dans l\'éducation',  # Nom affiché dans la légende
        marker_color='blue'  # Couleur des barres
    ))

    # Ajouter la deuxième série de données (Valeur_2)
    graphCountry2.add_trace(go.Bar(
        x=countryGraphData['year'],
        y=countryGraphData['lit_rate_adult_pct'],
        name='Pourcentage de la population lettrée',  # Nom affiché dans la légende
        marker_color='orange'  # Couleur des barres
    ))

    # Mettre les barres côte à côte
    graphCountry2.update_layout(
        barmode='group',  # Les barres sont côte à côte
        title='Comparaison des Valeurs 1 et 2 par Année',
        xaxis=dict(
            title='Année',
            tickmode='linear',  # Mode linéaire
            dtick=1  # Afficher les ticks tous les 5 ans
        ),
        yaxis_title='Valeur',
        legend_title='Type de Valeur',
        yaxis_range=[0,105]
    )
    
    return graphCountry2
#endregion

   
    #  iris.rename(columns={   "sepal.length": "sepal_length",
    #                     "sepal.width": "sepal_width",
    #                     "petal.length": "petal_length",
    #                     "petal.width": "petal_width"},
    #                         inplace = True)
downloadAndCleanDataset()

with open("data/clean/countries.geo.json", "r") as f:
    countries = json.load(f)

# Default values
year = 1999
country_name="France"
displayPrimaryOnMap = True

worldEducation = pds.read_csv("data/clean/cleaned-world-education-data.csv")

correlationData = getCorrelationData(worldEducation)
continentEducationData = getContinentEducationData(worldEducation,year)
worldEducationForMap, maxPupilTeacher = getMapData(worldEducation,year,displayPrimaryOnMap)
bubbleData = getBubbleData(worldEducation, year)
countryEducationData = worldEducation[worldEducation["country"]==country_name]


app = dash.Dash(__name__) 

#region callaback functions
@app.callback(
    [
        dash.Output(component_id='educationWorldMap', component_property='figure'),
        dash.Output(component_id='bubbleGraph', component_property='figure'),
        dash.Output(component_id='continentGDPGraph',component_property='figure')
        ],
    [dash.Input(component_id='year-dropdown', component_property='value')]
)
def updateYear(input_value):
    global displayPrimaryOnMap, worldEducationForMap, maxPupilTeacher, bubbleData, continentEducationData, year
    
    year = input_value
    
    bubbleData = getBubbleData(worldEducation, year)
    worldEducationForMap, maxPupilTeacher = getMapData(worldEducation,year,displayPrimaryOnMap)
    continentEducationData = getContinentEducationData(worldEducation, year)
    return [
                drawEducationWorldMap(worldEducationForMap,countries,displayPrimaryOnMap,maxPupilTeacher),
                drawBubbleGraph(bubbleData),
                drawContinentGDPGraph(continentEducationData)
            ]
    
@app.callback(
        dash.Output(component_id='educationWorldMap', component_property='figure', allow_duplicate=True),
    [dash.Input(component_id='map-button-elementary', component_property='n_clicks'),
     dash.Input(component_id='map-button-secondary', component_property='n_clicks')],
    prevent_initial_call=True
)
def changeMapSchoolType(elementary_button, secondary_button):
    global displayPrimaryOnMap, worldEducationForMap, year
    if 'map-button-elementary'== dash.ctx.triggered_id:
        displayPrimaryOnMap = True
    elif 'map-button-secondary'== dash.ctx.triggered_id:
        displayPrimaryOnMap = False
    worldEducationForMap, maxPupilTeacher = getMapData(worldEducation,year,displayPrimaryOnMap)
    return drawEducationWorldMap(worldEducationForMap,countries,displayPrimaryOnMap,maxPupilTeacher)

@app.callback(
    dash.Output(component_id='heatmap', component_property='figure'), 
    dash.Input(component_id='heatmap-switch', component_property='on')
)
def ToggleHeatMapText(on):
    return px.imshow(correlationData, text_auto=on)

# Now create the graph that updates the country name based on hover and showing Years on x-axis and Display value
# of chosen dataframe on y-axis
@app.callback(
    [dash.Output(component_id="countryCurveEvolution", component_property="figure"),
     dash.Output(component_id="country_graph2", component_property="figure")],
    dash.Input(component_id="educationWorldMap", component_property="clickData"),
)
def updateCountryBasedGraph(clickData):
    global country_name, countryEducationData
    if clickData is not None:
        country_name = clickData["points"][0]["hovertext"]
        countryEducationData = worldEducation[worldEducation["country"]==country_name]

    return [drawCountryCurveEvolution(countryEducationData), drawCountryGraph2(countryEducationData)]

#endregion

if __name__ == '__main__':    
    bubbleGraph = drawBubbleGraph(bubbleData)
    heatmap = px.imshow(correlationData, text_auto=False)
    educationWorldMap = drawEducationWorldMap(worldEducationForMap, countries, displayPrimaryOnMap, maxPupilTeacher)
    continentGDPGraph = drawContinentGDPGraph(continentEducationData)
    
    countryCurveEvolution = drawCountryCurveEvolution(countryEducationData)
    graphCountry2 = drawCountryGraph2(countryEducationData)
    
    app.layout = html.Div(children=[
                        html.H1(children=f'Données globales : ',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 
                        html.Label('Year'),
                        
                        dcc.Dropdown(
                            id="year-dropdown",
                            options=[
                                {'label': '1999', 'value': 1999},
                                {'label': '2000', 'value': 2000},
                                {'label': '2001', 'value': 2001},
                                {'label': '2002', 'value': 2002},
                                {'label': '2003', 'value': 2003},
                                {'label': '2004', 'value': 2004},
                                {'label': '2005', 'value': 2005},
                                {'label': '2006', 'value': 2006},
                                {'label': '2007', 'value': 2007},
                                {'label': '2008', 'value': 2008},
                                {'label': '2009', 'value': 2009},
                                {'label': '2010', 'value': 2010},
                                {'label': '2011', 'value': 2011},
                                {'label': '2012', 'value': 2012},
                                {'label': '2013', 'value': 2013},
                                {'label': '2014', 'value': 2014},
                                {'label': '2015', 'value': 2015},
                                {'label': '2016', 'value': 2016},
                                {'label': '2017', 'value': 2017},
                                {'label': '2018', 'value': 2018},
                                {'label': '2019', 'value': 2019},
                                {'label': '2020', 'value': 2020},
                            ],
                            value=year,
                        ),
                        html.H1(children=f'Heatmap de la corrélation entre les données du dataset',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 


                        html.Div(children=f'''
                            On peut voir que .... TODO .
                        '''), 
                        dcc.Graph(
                            id='heatmap',
                            figure=heatmap
                        ),
                        daq.BooleanSwitch(id='heatmap-switch', on=False, label="Afficher les valeurs"),
                        html.H1(children=f'Histogramme : ',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 
                        html.Div(children=f'''
                            On peut voir que .... TODO .
                        '''), 
                        dcc.Graph(
                            id='continentGDPGraph',
                            figure=continentGDPGraph
                        ),
                        html.H1(children=f'Ratio d\élèves par professeur en '+'élémentaire 'if displayPrimaryOnMap else 'secondaire'+' en ({year})',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 


                        html.Div(children=f'''
                            La carte ci-desosus montre le nombre moyen d'élèves par professeurs dans les différentes pays. Pour les pays n'ayant pas dedonnées en {year}, nous prenons les données les plus récentes en {year}.
                        '''), 
                        html.Button(id='map-button-elementary',children="Élémentaire"),
                        html.Button(id='map-button-secondary',children="Secondaire"),

                        dcc.Graph(
                            id='educationWorldMap',
                            figure=educationWorldMap
                        ), 
                                                
                        html.H1(children=f'Bubble graph des statistiques des écoles primaires par continent',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 


                        html.Div(children=f'''
                            On peut voir que .... TODO .
                        '''), 
                        dcc.Graph(
                            id='bubbleGraph',
                            figure=bubbleGraph
                        ),
                        
                        html.H1(children=f'Données concernant: '+country_name,
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 
                        html.H1(children=f'Courbe',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 


                        html.Div(children=f'''
                            On peut voir que .... TODO .
                        '''), 
                        dcc.Graph(
                            id='countryCurveEvolution',
                            figure=countryCurveEvolution
                        ),
                        
                        html.H1(children=f'Histogramme',
                                    style={'textAlign': 'center', 'color': '#7FDBFF'}), 


                        html.Div(children=f'''
                            On peut voir que .... TODO .
                        '''), 
                        dcc.Graph(
                            id='country_graph2',
                            figure=graphCountry2
                        ),

                    ]
                    )

    #
    # RUN APP
    #

    app.run_server(debug=True)