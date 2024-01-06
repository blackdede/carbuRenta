from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

heatmap_dataframe = pd.read_json("graph_data/data.json")

app = Dash(__name__)

# Add a list of fuel types available in your dataset
fuel_types = ["Gazole", "SP95", "E85", "E10", "SP98"]

days_len = len(heatmap_dataframe['stations'][0]['carburants'][fuel_types[0]])

# Create dropdown for fuel selection
fuel_dropdown = dcc.Dropdown(
    id='fuel-dropdown',
    options=[{'label': fuel, 'value': fuel} for fuel in fuel_types],
    value=fuel_types[0],  # Default value
)

# Create slider for selecting the index of the fuel prices list
slider = dcc.Slider(
    id='price-slider',
    min=0,
    max=days_len - 1,
    marks={i: str(i) for i in range(len(heatmap_dataframe['stations'][0]['carburants'][fuel_types[0]]))},
    value=0,  # Default value
)

def get_icicle():
    """
    Carte des noms de stations, afin de voir les marques qui ressortent le plus
    """
    station_names = {}

    for station in heatmap_dataframe['stations']:
        if station['name'] in station_names:
            station_names[station['name']] += 1
        else:
            station_names[station['name']] = 1

    df = pd.DataFrame(
        {
            'name': list(station_names.keys()),
            'count': list(station_names.values())
        }
    )

    fig = px.icicle(df, path=['name'], values='count', title='Nombre de stations par marque')
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))

    return fig

app.layout = html.Div([
    html.H1(children='Carburenta - Prix des carburants en France 🐀', style={'textAlign': 'center'}),
    
    # Add dropdown and slider to the layout
    fuel_dropdown,
    slider,
    
    # Update the graph based on dropdown and slider values
    dcc.Graph(id='heatmap'),
    dcc.Graph(id='histogram'),
    dcc.Graph(id='piechart'),
    dcc.Graph(id='markersmap'),
    dcc.Graph(id='icicle', figure=get_icicle())
])

@app.callback(
    Output('piechart', 'figure'),
    [Input('price-slider', 'value')]
)
def update_piechart(selected_price_index):
    """
    Grpahique en camembert qui montre le prix moyen de chaque carburant pour le jour selectionné
    """
    gas_average_prices = [0] * len(fuel_types)
    stations_lens = [0] * len(fuel_types)

    for station in heatmap_dataframe['stations']:
        for i in range(len(fuel_types)):
            if fuel_types[i] in station['carburants']:
                stations_lens[i] += 1
                gas_average_prices[i] += station['carburants'][fuel_types[i]][selected_price_index]

    for i in range(len(fuel_types)):
        gas_average_prices[i] /= stations_lens[i]

    df = pd.DataFrame(
        {
            'carburant': fuel_types,
            'prix': gas_average_prices
        }
    )

    fig = px.pie(df, values='prix', names='carburant', title=f'Prix moyen des carburants il y à {days_len - selected_price_index} jour(s)')

    return fig

@app.callback(
    Output('histogram', 'figure'),
    [Input('fuel-dropdown', 'value')]
)
def update_histogram(selected_fuel):
    # create a histogram of average values for each day
    prices_len = len(heatmap_dataframe['stations'][0]['carburants'][selected_fuel])
    average_prices = [0] * prices_len
    stations_len = 0

    for station in heatmap_dataframe['stations']:
        if selected_fuel in station['carburants']:
            stations_len += 1
            for i in range(prices_len):
                average_prices[i] += station['carburants'][selected_fuel][i]

    for i in range(prices_len):
        average_prices[i] /= stations_len

    df = pd.DataFrame(
        {
            'price': average_prices
        }
    )

    fig = px.bar(df, y="price", 
                 title=f'Histogramme des prix du {selected_fuel}',
                 labels={'price': 'Prix moyen (€)', 'index': 'il y a un an à aujourd\'hui'})

    return fig

# Define callback to update the heatmap based on dropdown and slider values
@app.callback(
    Output('heatmap', 'figure'),
    [Input('fuel-dropdown', 'value'), Input('price-slider', 'value')]
)
def update_heatmap(selected_fuel, selected_price_index):
    # Afficher sur une heatmap de densitée les stations les moins chères
    # Il s'agit d'une heatmap de densité, on ne peut pas régler la couleur en fonction du prix. On ne met donc pas toutes les stations car la carte est trop similaire peu importe le jour selectionné.
    
    average_price = 0.0
    stations_len = 0

    for station in heatmap_dataframe['stations']:
        if selected_fuel in station['carburants']:
            stations_len += 1
            average_price += station['carburants'][selected_fuel][selected_price_index]

    average_price /= stations_len

    stations = []

    for station in heatmap_dataframe['stations']:
        if selected_fuel in station['carburants']:
            if station['carburants'][selected_fuel][selected_price_index] <= average_price:
                stations.append(station)

    # Create a dataframe like a CSV with latitude, longitude and price columns for each station
    df = pd.DataFrame(
        {
            'latitude': [station['latitude'] for station in stations],
            'longitude': [station['longitude'] for station in stations],
            'price': [station['carburants'][selected_fuel][selected_price_index] for station in stations],
            'id': [station['id'] for station in stations],
        }
    )
    df = df.query('price != 0') # Remove stations with no price
    
    # Update the figure using Plotly Express
    fig = px.density_mapbox(df, 
                        lat='latitude', 
                        lon='longitude', 
                        z='price', 
                        radius=6,
                        center=dict(lat=46.939, lon=2.945), 
                        zoom=4,
                        mapbox_style="open-street-map",
                        title=f'Moitié des stations avec le prix du {selected_fuel} le plus bas',
                        hover_name='id')
    
    return fig

@app.callback(
    Output('markersmap', 'figure'),
    [Input('fuel-dropdown', 'value'), Input('price-slider', 'value')]
)
def update_markersmap(selected_fuel, selected_price_index):
    default_price = 0.0
    bound_top_left = (48.90415749721205, 2.450568379885376)
    bound_bottom_right = (48.79039931828495, 2.682282385717415)

    limited_stations = []

    for station in heatmap_dataframe['stations']:
        if selected_fuel in station['carburants'] and len(station['carburants'][selected_fuel]) > selected_price_index:
            if station['latitude'] <= bound_top_left[0] and station['latitude'] >= bound_bottom_right[0] and station['longitude'] >= bound_top_left[1] and station['longitude'] <= bound_bottom_right[1]:
                limited_stations.append(station)

    df = pd.DataFrame(
        [
        [
            station['latitude'] if station['latitude'] <= 90 and station['latitude'] >= -90 else 0,
            station['longitude'] if station['longitude'] <= 180 and station['longitude'] >= -180 else 0,
            station['carburants'][selected_fuel][selected_price_index] if selected_fuel in station['carburants'] and len(station['carburants'][selected_fuel]) > selected_price_index else default_price
        ] for station in limited_stations
    ],
    columns=['latitude', 'longitude', 'price'])

    fig = go.Figure(data=go.Scattergeo(
        locationmode="ISO-3",
        lon = df['longitude'],
        lat = df['latitude'],
        text = df['price'],
        mode = 'markers',
        marker = dict(
            size = 8,
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'square',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = 'Blues',
            cmin = 0,
            color = df['price'],
            cmax = df['price'].max(),
            colorbar_title=f'Prix du {selected_fuel}'
        )))

    fig.update_layout(
        title = 'Carte des stations autour de ESIEE Paris, colorées par prix',
        geo = dict(
            scope='europe',
            showland = True,
            landcolor = "rgb(250, 250, 250)",
            subunitcolor = "rgb(217, 217, 217)",
            countrycolor = "rgb(217, 217, 217)",
            countrywidth = 0.5,
            subunitwidth = 0.5, 
            projection_scale=400,
            center=dict(lat=48.847, lon=2.549),
        ),
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)