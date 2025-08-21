import plotly.graph_objs as go
import dash
from dash import html, dcc
import pandas as pd

def prepare_data_store_type(df):
    store_type_data = df
    weekday_order = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
    store_type_data['weekday'] = df['tran_date'].dt.weekday.map({0:'Poniedziałek',1:'Wtorek',2:'Środa', 3:'Czwartek',4:'Piątek',5:'Sobota',6:'Niedziela'})
    store_type_data = store_type_data.groupby(['weekday', 'Store_type'])['total_amt'].sum().reset_index()
    store_type_data['weekday'] = pd.Categorical(store_type_data['weekday'], categories=weekday_order, ordered=True)
    store_type_data = store_type_data.sort_values(by='weekday')
    return store_type_data


def prepare_data_customers(df,value):
    customers_df = prepare_customers_df(df)
    customers_df = customers_df[(customers_df['age'] >= value[0]) & (customers_df['age'] <= value[1])]
    customers_df = customers_df.groupby(['Store_type'])['total_amt'].sum().reset_index()
    return customers_df

def prepare_customers_df(df):
    df['DOB'] = pd.to_datetime(df['DOB'])
    customers_df = df
    customers_df['age'] = round((customers_df['tran_date'] - customers_df['DOB']).dt.days / 365)
    return customers_df


def render_tab(df):
    customers_df = prepare_customers_df(df)
    layout = html.Div([html.H1('Kanały sprzedaży',style={'text-align':'center'}),
                        html.Div([html.Div([dcc.Graph(id='store-type-heatmap')],style={'width': '50%', 'padding-right': '10px'}),
                        html.Div([dcc.Graph(id='pie-customer-age')],style={'width': '50%', 'padding-left': '10px', 'text-align': 'right'})], style={'display': 'flex', 'flex-wrap': 'nowrap'}),
                         html.Div([html.Div([html.Label("Przedział czasowy", style={'display': 'block', 'margin-bottom': '10px'}),
                                            dcc.DatePickerRange(id='store-type-range',
                                            start_date=df['tran_date'].min(),
                                            end_date=df['tran_date'].max(),
                                            display_format='YYYY-MM-DD')],style={'width': '50%', 'text-align':'center'}),
                        html.Div([html.Label("Wiek klienta", style={'display': 'block', 'margin-bottom': '10px'}),
                            dcc.RangeSlider(id='age-slider', min=customers_df['age'].min(), max=customers_df['age'].max(), step=2, value=[customers_df['age'].min(), customers_df['age'].max()])
                            ], style={'width': '50%', 'padding-left': '10px', 'text-align': 'right'})], style={'display': 'flex', 'flex-wrap': 'nowrap'})],
                        style={'padding': '20px'}
                        )

    return layout