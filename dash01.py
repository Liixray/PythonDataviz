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


def downloadAndCleanDataset():
    # Download the raw dataset
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files('bushraqurban/world-education-dataset', path='data/raw', unzip=True)

    # Add continent informations to the default dataset
    rawCountryContinentData = pds.read_csv("data/raw/country-and-continent-codes-list.csv")
    rawWorldEducationData = pds.read_csv("data/raw/world-education-data.csv")
    cleanWorldEducationData = pds.merge(rawWorldEducationData, rawCountryContinentData[["Continent_Name","Three_Letter_Country_Code"]], left_on="country_code", right_on="Three_Letter_Country_Code")
    cleanWorldEducationData.to_csv("data/clean/cleaned-world-education-data.csv")
    
def getMapData(baseData,year,displayPrimary):
    columnName= "pupil_teacher_primary" if displayPrimary else "pupil_teacher_secondary"
    worldEducationForMap = baseData[(baseData[columnName].notna())&(baseData["year"]<=year)]
    worldEducationForMap = worldEducationForMap.sort_values(by=['country','year'],ascending=[True,False])
    worldEducationForMap = worldEducationForMap.drop_duplicates(subset="country",keep="first")
    maxPupilTeacher = worldEducationForMap[columnName].max()
    return worldEducationForMap, maxPupilTeacher
#
# Data
#

    
    #  iris.rename(columns={   "sepal.length": "sepal_length",
    #                     "sepal.width": "sepal_width",
    #                     "petal.length": "petal_length",
    #                     "petal.width": "petal_width"},
    #                         inplace = True)
downloadAndCleanDataset()
with open("data/clean/countries.geo.json", "r") as f:
    counties = json.load(f)
year = 1999
# country_name="Korea, Rep."
country_name="Turkiye"
displayPrimaryOnMap = True
worldEducation = pds.read_csv("data/clean/cleaned-world-education-data.csv")
# print(countryContinent['Three_Letter_Country_Code'])


worldEducationByYear = worldEducation[ worldEducation["year"]==year ]
worldEducationForMap, maxPupilTeacher = getMapData(worldEducation,year,displayPrimaryOnMap)

continentEducation = worldEducation[(worldEducation['gov_exp_pct_gdp'].notna())&(worldEducation["year"]<=year)]
continentEducation = continentEducation.sort_values(by=['country','year'],ascending=[True,False])
continentEducation = continentEducation.drop_duplicates(subset="country",keep="first")
continentEducation = continentEducation.groupby('Continent_Name')['gov_exp_pct_gdp'].mean().reset_index()
# print(continentEducation)


# Afficher le résultat


gapminder = px.data.gapminder() # (1)
years = gapminder["year"].unique()
app = dash.Dash(__name__) # (3)
a = worldEducation.select_dtypes(include=[np.number])
corr= a.corr().round(2)
# print(data)
worldEducationForCountry = worldEducation[worldEducation["country"]==country_name]

# print(worldEducationForCountry)
# print(countryContinent[countryContinent["Three_Letter_Country_Code"]==worldEducation[worldEducation["country"]=="Japan"]["country_code"]])


### BULLES ###

bubbleData = worldEducationByYear
bubbleData['gov_exp_pct_gdp'] = bubbleData['gov_exp_pct_gdp'].fillna(0).astype(float)

### FIN BULLES ###


@app.callback(
    [
        # dash.Output(component_id='graph1', component_property='figure'),
        dash.Output(component_id='graph2', component_property='figure'),
        dash.Output(component_id='bubbleGraph', component_property='figure'),
        ], # (1)
    [dash.Input(component_id='year-slider', component_property='value'),
     dash.Input(component_id='map-button-elementary', component_property='n_clicks'),
     dash.Input(component_id='map-button-secondary', component_property='n_clicks')] # (2)
)
def update_map(input_value, elementary_button, secondary_button): # (3)
    global displayPrimaryOnMap, worldEducationForMap, maxPupilTeacher, bubbleData
    if 'map-button-elementary'== dash.ctx.triggered_id:
        displayPrimaryOnMap = True
    elif 'map-button-secondary'== dash.ctx.triggered_id:
        displayPrimaryOnMap = False
        
    bubbleData = worldEducation[ worldEducation["year"]==input_value]
    bubbleData['gov_exp_pct_gdp'] = bubbleData['gov_exp_pct_gdp'].fillna(0).astype(float)
    
    worldEducationForMap, maxPupilTeacher = getMapData(worldEducation,input_value,displayPrimaryOnMap)
    return [
                px.choropleth_map(worldEducationForMap, geojson=counties, locations='country_code', 
                                  color='pupil_teacher_primary' if displayPrimaryOnMap else 'pupil_teacher_secondary',
                                    color_continuous_scale="YlGnBu",
                                    range_color=(0, maxPupilTeacher),
                                    map_style="carto-positron",
                                    zoom=1, center = {"lat": 37.0902, "lon": -95.7129},
                                    opacity=0.5,
                           hover_data="country_code",
                           hover_name="country",
                           labels={'pupil_teacher_primary' if displayPrimaryOnMap else 'pupil_teacher_secondary':'Nombre d\'élèves par professeurs'}
                                    ),
                px.scatter(
                bubbleData,
                x="school_enrol_primary_pct",
                y="pri_comp_rate_pct",
                size="gov_exp_pct_gdp",
                hover_name="country",
                color=bubbleData["Continent_Name"],
                color_discrete_map={"Africa":'#5bb73b',
                            "Asia":"#ffeb28",
                            "Europe":"#4330e1",
                            "North America":'#ed431f',
                            "Oceania":"#8b26b7",
                            "South America":"#f99f2c"}
                )
            ]

@app.callback(
    dash.Output(component_id='heatmap', component_property='figure'), # (1)
    dash.Input(component_id='heatmap-switch', component_property='on') # (2)
)
def toggle_heatmap_text(on):
    # print(on)
    return px.imshow(corr, text_auto=on)

# Now create the graph that updates the country name based on hover and showing Years on x-axis and Display value
# of chosen dataframe on y-axis
@app.callback(
    [dash.Output(component_id="country_graph", component_property="figure"),
     dash.Output(component_id="country_graph2", component_property="figure")],
    dash.Input(component_id="graph2", component_property="clickData")
)
def create_graph(clickData): #, dataframe_dropdown, residence_area_type
    # print(clickData)
    global country_name, worldEducationForCountry
    if clickData is not None:
        country_name = clickData["points"][0]["hovertext"]
        worldEducationForCountry = worldEducation[worldEducation["country"]==country_name]
    
    graphCountry = px.line(worldEducationForCountry,x="year",y=["school_enrol_primary_pct","school_enrol_secondary_pct","school_enrol_tertiary_pct","lit_rate_adult_pct"],range_y=[0,max(105,worldEducationForCountry[["school_enrol_primary_pct","school_enrol_secondary_pct","school_enrol_tertiary_pct","lit_rate_adult_pct"]].max().max()+5)])
    
    
    graphCountry2 = go.Figure()

    # Ajouter la première série de données (Valeur_1)
    graphCountry2.add_trace(go.Bar(
        x=worldEducationForCountry['year'],
        y=worldEducationForCountry['gov_exp_pct_gdp'],
        name='Pourcentage du PB investi dans l\'éducation',  # Nom affiché dans la légende
        marker_color='blue'  # Couleur des barres
    ))

    # Ajouter la deuxième série de données (Valeur_2)
    graphCountry2.add_trace(go.Bar(
        x=worldEducationForCountry['year'],
        y=worldEducationForCountry['lit_rate_adult_pct'],
        name='Pourcentage de la population lettrée',  # Nom affiché dans la légende
        marker_color='orange'  # Couleur des barres
    ))

    
    return [graphCountry.update_traces(connectgaps=True), graphCountry2.update_layout(
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
]
if __name__ == '__main__':
    # bubbleGraph = px.scatter(gapminder.query(f"year=={year}"), x="school_enrol_primary_pct", y="pri_comp_rate_pct", size="gov_exp_pct_gdp", hover_name="")

    
    b = px.scatter(
        bubbleData,
        x="school_enrol_primary_pct",
        y="pri_comp_rate_pct",
        size="gov_exp_pct_gdp",
        hover_name="country",
        color=bubbleData["Continent_Name"],
        color_discrete_map={"Africa":'#5bb73b',
                            "Asia":"#ffeb28",
                            "Europe":"#4330e1",
                            "North America":'#ed431f',
                            "Oceania":"#8b26b7",
                            "South America":"#f99f2c"}
    )
    
    heatmap = px.imshow(corr, text_auto=False)
    fig2 = px.choropleth_map(worldEducationForMap, geojson=counties, locations='country_code', 
                                  color='pupil_teacher_primary' if displayPrimaryOnMap else 'pupil_teacher_secondary',
                                    color_continuous_scale="YlGnBu",
                                    range_color=(0, maxPupilTeacher),
                                    map_style="carto-positron",
                                    zoom=1, center = {"lat": 37.0902, "lon": -95.7129},
                                    opacity=0.5,
                           hover_data="country_code",
                           hover_name="country",
                           labels={'pupil_teacher_primary' if displayPrimaryOnMap else 'pupil_teacher_secondary':'Nombre d\'élèves par professeurs'}
                                    )
    graphContinent = px.histogram(continentEducation,x="Continent_Name",y="gov_exp_pct_gdp",color=continentEducation["Continent_Name"])
    graphCountry = px.line(worldEducationForCountry,x="year",y=["school_enrol_primary_pct","school_enrol_secondary_pct","school_enrol_tertiary_pct","lit_rate_adult_pct"],range_y=[0,max(105,worldEducationForCountry[["school_enrol_primary_pct","school_enrol_secondary_pct","school_enrol_tertiary_pct","lit_rate_adult_pct"]].max().max()+5)])
    graphCountry.update_traces(connectgaps=True)
    
    graphCountry2 = go.Figure()

    # Ajouter la première série de données (Valeur_1)
    graphCountry2.add_trace(go.Bar(
        x=worldEducationForCountry['year'],
        y=worldEducationForCountry['gov_exp_pct_gdp'],
        name='Pourcentage du PB investi dans l\'éducation',  # Nom affiché dans la légende
        marker_color='blue'  # Couleur des barres
    ))

    # Ajouter la deuxième série de données (Valeur_2)
    graphCountry2.add_trace(go.Bar(
        x=worldEducationForCountry['year'],
        y=worldEducationForCountry['lit_rate_adult_pct'],
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
    
    app.layout = html.Div(children=[
                        ######### Titre de la page #########
                        html.Div(children=[
                            html.Div(children=[
                                html.H1(children="World Education DashBoard"),
                                html.H2(children="Idrissi Nidal - Leveque Lucas"),
                            ], className="titles"),
                        ], className="hero"),
                        ####################################

                        
                        ################ Les deux premiers graphiques  ################
                        # Row avec les deux premiers graphiques
                        html.Div(children=[
                            # Column pour la heatmap et le switch
                            html.Div(children=[
                                dcc.Graph(
                                    id='heatmap',
                                    figure=heatmap
                                ),
                                
                                daq.BooleanSwitch(id='heatmap-switch', on=False, label="Afficher les valeurs"),
                            ], className="column"),
                            
                            # Histogramme 
                            dcc.Graph(
                                id='graphContinent',
                                figure=graphContinent
                            ),
                        ], className="row"),
                        ################################################################
                        
                        ################## Graphs avec dates #####################
                        html.Div(children=[
                            html.H3(children="Select a year", className="slider-title"),
                            
                            html.Div(children=[
                                dcc.Slider(
                                    id='year-slider',
                                    min=1999,
                                    max=2020,
                                    step=1,
                                    marks={year: str(year) for year in range(1999, 2021)},
                                    value=year,  # Année sélectionnée par défaut
                                ),
                            ], className="slider-bg"),  
                            
                            html.Div(children=[
                                html.H3(children="Ceci est un titre", className="section-title"),
                                html.Div(children=f'''
                                    La carte ci-desosus montre le nombre moyen d'élèves par professeurs dans les différentes pays. Pour les pays n'ayant pas dedonnées en {year}, nous prenons les données les plus récentes en {year}.
                                '''), # (7)
                                
                                html.Div(children=[
                                    html.Button(id='map-button-elementary',children="Élémentaire", className="button"),
                                    html.Button(id='map-button-secondary',children="Secondaire", className="button"),
                                ], className="buttons"),
                                
                                dcc.Graph(
                                    id='graph2',
                                    figure=fig2,
                                ), # (6)
                            ], className="paragraph"),
                            
                            
                            html.Div(children=[
                                html.H3(children="Ceci est un titre", className="section-title"),
                                dcc.Graph(
                                    id='bubbleGraph',
                                    figure=b
                                ),
                            ], className="paragraph"),
                            
                            
                            html.Div(children=[
                                html.H3(children="Ceci est un titre", className="section-title"),
                                dcc.Graph(
                                    id='country_graph',
                                    figure=graphCountry
                                ),
                            ], className="paragraph"),
                            
                            
                            html.Div(children=[
                            html.H3(children="Ceci est un titre", className="section-title"),
                            dcc.Graph(
                                id='country_graph2',
                                figure=graphCountry2
                            ),
                            ], className="paragraph"),
                            
                        ], className="year-graphs-cont"),
                        
                        # html.H1(children=f'Heatmap de la corrélation entre les données du dataset',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)


                        # html.Div(children=f'''
                        #     On peut voir que .... TODO .
                        # '''), # (7)
                        
                        # html.H1(children=f'Histogramme : ',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)
                        # html.Div(children=f'''
                        #     On peut voir que .... TODO .
                        # '''), # (7)
                        
                        # html.H1(children=f'Ratio d\élèves par professeur en '+'élémentaire 'if displayPrimaryOnMap else 'secondaire'+' en ({year})',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)

                                                
                        # html.H1(children=f'Bubble graph des statistiques des écoles primaires par continent',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)


                        # html.Div(children=f'''
                        #     On peut voir que .... TODO .
                        # '''), # (7)
                        
                        
                        # html.H1(children=f'Données concernant: '+country_name,
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)
                        # html.H1(children=f'Courbe',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)


                        # html.Div(children=f'''
                        #     On peut voir que .... TODO .
                        # '''), # (7)
                        
                        
                        # html.H1(children=f'Histogramme',
                        #             style={'textAlign': 'center', 'color': '#7FDBFF'}), # (5)


                        # html.Div(children=f'''
                        #     On peut voir que .... TODO .
                        # '''), # (7)
                        

                    ], className="cont")

    #
    # RUN APP
    #

    app.run_server(debug=True) # (8)