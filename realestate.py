import pandas as pd
import plotly.express as px
import json
import dash  
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

df = pd.read_csv('flat_database.csv')
with open('dzielniceWAW.geojson', "r",encoding='utf-8') as read_file:
    warsaw = json.load(read_file)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
server = app.server

df1 = df.copy()
df1['Size1'] = pd.cut(df1['Price in PLN'], [-10,200000,300000,400000,500000,750000,1000000,1500000,1000000000], labels=False)
df1['Location'] = df1['Location'].fillna('Out of Warsaw')
fig1= px.scatter_mapbox(df1, lon=df1['Dlugosc'], lat=df1['Szerokosc'], 
                color=df1['Location'], size=df1['Size1'],
                hover_data={'Size1':False,
                            'Szerokosc':False,
                            'Dlugosc':False,
                            'Location':False,
                            'Price in PLN':True,
                            'No. of rooms':True,
                            'Flat area in m2':True,
                            },
                hover_name=df1['Location'], 
                opacity=0.7, zoom=10)    

fig1.update_layout(mapbox_style="carto-positron", legend_title_text='District',
                    legend_title_font_size=20, hoverlabel_font_family='Arial',
                    margin={"r":0,"t":0,"l":0,"b":0}, showlegend=True)

options1=[
    {'label': 'No. of flats', 'value': 'No. of flats'},
    {'label': 'Price in PLN', 'value': 'Price in PLN'},
    {'label': 'Price per meter', 'value': 'Price per meter'},
    {'label': 'Floors in the building', 'value': 'Floors in the building'},
    {'label': 'Floor', 'value': 'Floor'},
    {'label': 'No. of rooms', 'value': 'No. of rooms'},
    {'label': 'Flat area in m2', 'value': 'Flat area in m2'}
]

options2=[
    {'label': 'Median', 'value': 0.5},
    {'label': '25-percentile', 'value': 0.25},
    {'label': '75-percentile', 'value': 0.75} 
]

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([ 
            html.Br(),
            html.Br(),
            html.H1(children='Flats in Warsaw primary market', 
                    className='text-center mb-4')
        ], width={'size':7, 'offset':2}),
        dbc.Col([
            html.Br(),
            html.Br(),
            dbc.Button('Get code from GitHub', id='github-link',
                       href='https://github.com/AleksanderSzok/Dash-Plotly', target='_blank', color="primary")
        ], width=3)
    ], className='h-25'),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='demo-dropdown',
                value='Price in PLN',
                clearable=False
            ),
            html.Br(),
            html.Br(),
            dcc.Dropdown(
                id='quantile_drop',
                value=0.5,
                clearable=False,
            )],
        width={'size':2, 'offset':1}),

        dbc.Col([
            dcc.Graph(
                id='example-graph',
                figure={},
                config={}
            )],
        width=6),

        dbc.Col([
            dbc.Button('Show/hide map', id='submit-val', color="success", n_clicks=0)],
        width=3)
    ], justify='center', className='h-75')
], fluid=True, className='dash-bootstrap', style={"height": "100vh"})

@app.callback(
    [Output(component_id='quantile_drop', component_property='disabled'),
    Output(component_id='demo-dropdown', component_property='disabled'),
    Output(component_id='quantile_drop', component_property='options'),
    Output(component_id='demo-dropdown', component_property='options'),
    Output(component_id='demo-dropdown', component_property='className'),
    Output(component_id='quantile_drop', component_property='className')],
    [Input(component_id='demo-dropdown', component_property='value'),
    Input(component_id='submit-val', component_property='n_clicks')]
)
def disable_drop(val, nclicks):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == 'submit-val':
        if nclicks%2 == 1:
            return True, True, [{'label':' ','value': 0.5}], [{'label':' ','value': 'Price in PLN'}], 'hov1', 'hov1'

    if val == 'No. of flats':
        return True, False, [{'label':' ','value': 0.5}], options1, None, 'hov1'
    else:
        return False, False, options2 , options1, None, None

@app.callback(
    [Output(component_id='example-graph', component_property='figure'),
    Output(component_id='example-graph', component_property='config')],
    [Input(component_id='demo-dropdown', component_property='value'),
    Input(component_id='quantile_drop', component_property='value'),
    Input(component_id='submit-val', component_property='n_clicks')]
)
def update_graph(value, value1, nclicks):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == 'submit-val':
        if nclicks%2 == 1:
            return fig1, {'scrollZoom': True }
        else:
            return graf(value, value1), {'scrollZoom': False }
    else:
        return graf(value, value1), {'scrollZoom': False }
 
def graf(value, value1):
    dff = df.copy()
    
    if value == 'No. of flats':
        dff = dff.loc[:,['Price in PLN','Location']].groupby(['Location'], as_index=False).count()
        dff.rename(columns={'Price in PLN':'No. of flats'}, inplace=True)
    else:  
        if value in ['Price in PLN', 'Price per meter']:
            dff = dff.loc[df['Price per meter'] > 1,:]
        dff = dff.groupby(['Location'], as_index=False).quantile(float(value1))
        dff = dff.round({'Price in PLN':0, 'Price per meter':0, 'Flat area in m2':2})

    fig = px.choropleth(dff, geojson=warsaw, color=value,
                        locations="Location", featureidkey="properties.nazwa_dzie",
                        projection="mercator",
                        range_color=[dff[value].min(), dff[value].max()]
                    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar =dict(
                    bgcolor="darksalmon",
                    tickfont=dict(color='white')
                    ),
                    coloraxis_colorbar_title_font_size=14,
                    hoverlabel=dict(
                                    bgcolor="white",
                                    font_size=16,
                                    font_family="Rockwell"
                                )
                    )
    return fig
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)



