from datetime import timedelta, datetime
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

app = Dash(__name__)

def get_piechart(selected_stations):
    """
    Diagramme en camembert pour afficher la distribution des stations par marque
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
    
    # Sort the dataframe by count in descending order
    df = df.sort_values(by='count', ascending=False)
    

    # Limit the dataframe to the top X rows
    df = df.head(selected_stations)

    df['hover_text'] = (
        'Nom de la marque: ' + df['name'] +
        '<br>Nombre de stations: ' + df['count'].astype(str)
    )

    fig = px.pie(df, names='name', values='count', title='Distribution des stations par marque',
                 hover_data=['hover_text'], hover_name='name')

    # Update the hover template
    fig.update_traces(
        hovertemplate="Nom de la marque: %{label} <br>Nombre de stations: %{value} <br>Pourcentage: %{percent}",
    )
    return fig

@app.callback(
    Output('piechartNameStations', 'figure'),
    [Input('stations-dropdown', 'value')]
)
def update_piechart(selected_stations):
    return get_piechart(selected_stations)

@app.callback(
    Output('piechartPriceStations', 'figure'),
    [Input('date-picker', 'date')]
)
def update_piechart(selected_date):
    selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_price_index = (selected_date - datetime(2023, 1, 1)).days

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

    fig = px.pie(df, values='prix', names='carburant', title=f'Prix moyen des carburants le {selected_date.strftime("%Y-%m-%d")}')
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

    # Convert the day index to date
    start_date = datetime(2023, 1, 1)  # Assuming the data starts on January 1, 2023
    date_labels = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(prices_len)]

    df = pd.DataFrame(
        {
            'date': date_labels,
            'price': average_prices
        }
    )

    fig = px.bar(df, x="date", y="price",
                 title=f'Histogramme des prix du {selected_fuel}',
                 labels={'price': 'Prix moyen (€)', 'date': 'Date'})

    return fig

# Define callback to update the heatmap based on dropdown and slider values
@app.callback(
    Output('heatmap', 'figure'),
    [Input('fuel-dropdown', 'value'), Input('date-picker', 'date')]
)
def update_heatmap(selected_fuel, selected_date):
    # Convert the selected date to the corresponding index
    selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_price_index = (selected_date - datetime(2023, 1, 1)).days
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
                        hover_name='id',
                        labels={'price': 'Prix moyen (€)'})
    
    return fig

@app.callback(
    Output('markersmap', 'figure'),
    [Input('fuel-dropdown', 'value'), Input('date-picker', 'date')]
)
def update_markersmap(selected_fuel, selected_date):
    selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_price_index = (selected_date - datetime(2023, 1, 1)).days
    
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

    fig = go.Figure(go.Scattermapbox(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=8,
            opacity=0.8,
            color=df['price'],
            colorscale='bluered',
            cmin=df['price'].min(),
            cmax=df['price'].max(),
            colorbar=dict(title=f'Prix du {selected_fuel}')
        ),
        text=df['price']
    ))

    fig.update_layout(
        title='Carte des stations autour de ESIEE Paris, colorées par prix',
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=48.847, lon=2.549),
            zoom=12,
        ),
    )

    return fig

heatmap_dataframe = pd.read_json("graph_data/data.json")



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
date_picker = dcc.DatePickerSingle(
    id='date-picker',
    min_date_allowed=datetime(2023, 1, 1),
    max_date_allowed=datetime(2023, 12, 31),
    initial_visible_month=datetime(2023, 12, 31),
    date=datetime(2023, 12, 31).strftime("%Y-%m-%d")  # Use string representation
)

stations_dropdown = dcc.Dropdown(
    id='stations-dropdown',
    options=[
        {'label': 'Top 5', 'value': 5},
        {'label': 'Top 10', 'value': 10},
        {'label': 'Top 15', 'value': 15},
        {'label': 'Top 20', 'value': 20},
        {'label': 'Top 25', 'value': 25},
    ],
    value=15  # Default value
)

app.layout = html.Div([
    html.H1(children='Carburenta - Prix des carburants en France 🐀', style={'textAlign': 'center'}),
    
    # Add dropdown and date picker to the layout
    fuel_dropdown,
    date_picker,
    
    # Update the graph based on dropdown and date picker values
    dcc.Graph(id='heatmap'),
    dcc.Graph(id='histogram'),
    dcc.Graph(id='piechartPriceStations'),
    dcc.Graph(id='markersmap'),
    stations_dropdown,
    dcc.Graph(id='piechartNameStations', figure=get_piechart(15))

])

if __name__ == '__main__':
    app.run(debug=True)