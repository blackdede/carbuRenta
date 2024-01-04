from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

heatmap_dataframe = pd.read_json("graph_data/data.json")

app = Dash(__name__)

# Add a list of fuel types available in your dataset
fuel_types = ["Gazole", "SP95", "E85", "E10", "SP98"]

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
    max=len(heatmap_dataframe['stations'][0]['carburants'][fuel_types[0]]) - 1,
    marks={i: str(i) for i in range(len(heatmap_dataframe['stations'][0]['carburants'][fuel_types[0]]))},
    value=0,  # Default value
)

app.layout = html.Div([
    html.H1(children='Carburenta - Prix des carburants en France 🐀', style={'textAlign': 'center'}),
    
    # Add dropdown and slider to the layout
    fuel_dropdown,
    slider,
    
    # Update the graph based on dropdown and slider values
    dcc.Graph(id='heatmap'),
    dcc.Graph(id='histogram'),
])

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
    [Input('fuel-dropdown', 'value'),
     Input('price-slider', 'value')]
)
def update_heatmap(selected_fuel, selected_price_index):
    # TODO: Afficher uniquement les stations les moins chères pour chaque carburant, vu qu'il s'agit d'une carte de densité dont la couleur ne reflète pas le prix

    # Create a dataframe like a CSV with latitude, longitude and price columns for each station
    default_price = 0.0
    df = pd.DataFrame(
        [
        [
            station['latitude'] if station['latitude'] <= 90 and station['latitude'] >= -90 else 0,
            station['longitude'] if station['longitude'] <= 180 and station['longitude'] >= -180 else 0,
            station['carburants'][selected_fuel][selected_price_index] if selected_fuel in station['carburants'] and len(station['carburants'][selected_fuel]) > selected_price_index else default_price
        ] for station in heatmap_dataframe['stations']
    ],
    columns=['latitude', 'longitude', 'price'])

    custom_color_scale = [
        [0.0, 'blue'],
        [0.2, 'green'],
        [0.4, 'yellow'],
        [0.6, 'orange'],
        [0.8, 'red'],
        [1.0, 'darkred']
    ]
    
    # Update the figure using Plotly Express
    fig = px.density_mapbox(df, 
                        lat='latitude', 
                        lon='longitude', 
                        z='price', 
                        radius=15,
                        center=dict(lat=46.939, lon=2.945), 
                        zoom=4,
                        mapbox_style="open-street-map",
                        color_continuous_scale=custom_color_scale,
                        title=f'Carte des prix du {selected_fuel}')

    # fig = go.Figure(data=go.Scattergeo(
    #     locationmode="ISO-3",
    #     lon = df['longitude'],
    #     lat = df['latitude'],
    #     text = df['price'],
    #     mode = 'markers',
    #     marker = dict(
    #         size = 8,
    #         opacity = 0.8,
    #         reversescale = True,
    #         autocolorscale = False,
    #         symbol = 'square',
    #         line = dict(
    #             width=1,
    #             color='rgba(102, 102, 102)'
    #         ),
    #         colorscale = 'Blues',
    #         cmin = 0,
    #         color = df['price'],
    #         cmax = df['price'].max(),
    #         colorbar_title=f'Prix du {selected_fuel}'
    #     )))

    # fig.update_layout(
    #     title = 'Prix du carburant par station',
    #     geo = dict(
    #         scope='europe',
    #         showland = True,
    #         landcolor = "rgb(250, 250, 250)",
    #         subunitcolor = "rgb(217, 217, 217)",
    #         countrycolor = "rgb(217, 217, 217)",
    #         countrywidth = 0.5,
    #         subunitwidth = 0.5,
    #     ),
    # )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True)