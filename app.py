import pandas as pd
import datetime as dt
import os
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash as dash_auth
import plotly.graph_objs as go
import tab1
import tab2
import dash_auth
import tab3

class db:
    def __init__(self):
        self.transactions = db.transation_init()
        self.cc = pd.read_csv(r'db\country_codes.csv',index_col=0)
        self.customers = pd.read_csv(r'db\customers.csv',index_col=0)
        self.prod_info = pd.read_csv(r'db\prod_cat_info.csv')


    @staticmethod
    def transation_init():
        transactions = pd.DataFrame()
        # p = os.path.join('db', 'transactions')
        src = r'db\transactions'
        for filename in os.listdir(src):
            transactions = pd.concat([transactions, pd.read_csv(os.path.join(src,filename),index_col=0)])

        def convert_dates(x):
            try:
                return dt.datetime.strptime(x,'%d-%m-%Y')
            except:
                return dt.datetime.strptime(x,'%d/%m/%Y')

        transactions['tran_date'] = transactions['tran_date'].apply(lambda x: convert_dates(x))

        return transactions
    
    def merge(self):
        df = self.transactions.join(self.prod_info.drop_duplicates(subset=['prod_cat_code'])
        .set_index('prod_cat_code')['prod_cat'],on='prod_cat_code',how='left')

        df = df.join(self.prod_info.drop_duplicates(subset=['prod_sub_cat_code'])
        .set_index('prod_sub_cat_code')['prod_subcat'],on='prod_subcat_code',how='left')

        df = df.join(self.customers.join(self.cc,on='country_code')
        .set_index('customer_Id'),on='cust_id')

        self.merged = df

        
df = db()
df.merge()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

app.layout = html.Div([html.Div([dcc.Tabs(id='tabs',value='tab-1',children=[
                            dcc.Tab(label='Sprzedaż globalna',value='tab-1'),
                            dcc.Tab(label='Produkty',value='tab-2'),
                            dcc.Tab(label='Kanały sprzedaży',value='tab-3')
                            ]),
                            html.Div(id='tabs-content')
                    ],style={'width':'80%','margin':'auto'})])

@app.callback(Output('tabs-content','children'),[Input('tabs','value')])
def render_content(tab):

    if tab == 'tab-1':
        return tab1.render_tab(df.merged)
    elif tab == 'tab-2':
        return tab2.render_tab(df.merged)
    elif tab == 'tab-3':
        return tab3.render_tab(df.merged)
    
## tab1 callbacks
@app.callback(Output('bar-sales','figure'),
    [Input('sales-range','start_date'),Input('sales-range','end_date')])
def tab1_bar_sales(start_date,end_date):

    truncated = df.merged[(df.merged['tran_date']>=start_date)&(df.merged['tran_date']<=end_date)]
    grouped = truncated[truncated['total_amt']>0].groupby([pd.Grouper(key='tran_date',freq='M'),'Store_type'])['total_amt'].sum().round(2).unstack()

    traces = []
    for col in grouped.columns:
        traces.append(go.Bar(x=grouped.index,y=grouped[col],name=col,hoverinfo='text',
        hovertext=[f'{y/1e3:.2f}k' for y in grouped[col].values]))

    data = traces
    fig = go.Figure(data=data,layout=go.Layout(title='Przychody',barmode='stack',legend=dict(x=0,y=-0.5)))

    return fig


@app.callback(Output('choropleth-sales','figure'),
            [Input('sales-range','start_date'),Input('sales-range','end_date')])
def tab1_choropleth_sales(start_date,end_date):

    truncated = df.merged[(df.merged['tran_date']>=start_date)&(df.merged['tran_date']<=end_date)]
    grouped = truncated[truncated['total_amt']>0].groupby('country')['total_amt'].sum().round(2)

    trace0 = go.Choropleth(colorscale='Viridis',reversescale=True,
                            locations=grouped.index,locationmode='country names',
                            z = grouped.values, colorbar=dict(title='Sales'))
    data = [trace0]
    fig = go.Figure(data=data,layout=go.Layout(title='Mapa',geo=dict(showframe=False,projection={'type':'natural earth'})))
    fig.update_layout(height=400)

    return fig


## tab2 callbacks
@app.callback(Output('barh-prod-subcat','figure'),
            [Input('prod_dropdown','value')])
def tab2_barh_prod_subcat(chosen_cat):

    grouped = df.merged[(df.merged['total_amt']>0)&(df.merged['prod_cat']==chosen_cat)].pivot_table(index='prod_subcat',columns='Gender',values='total_amt',aggfunc='sum').assign(_sum=lambda x: x['F']+x['M']).sort_values(by='_sum').round(2)

    traces = []
    for col in ['F','M']:
        traces.append(go.Bar(x=grouped[col],y=grouped.index,orientation='h',name=col))

    data = traces
    fig = go.Figure(data=data,layout=go.Layout(barmode='stack',margin={'t':20,}))
    fig.update_layout(height=400)
    return fig


## tab3 callbacks
@app.callback(Output('store-type-heatmap','figure'),
            [Input('store-type-range','start_date'),Input('store-type-range','end_date')])
def tab3_store_type(start_date,end_date):

    df_merged_range = df.merged[(df.merged['tran_date']>=start_date)&(df.merged['tran_date']<=end_date)]
    store_type_data = tab3.prepare_data_store_type(df_merged_range)

    trace0 = go.Heatmap(x=store_type_data['weekday'],
                         y=store_type_data['Store_type'],
                         z=store_type_data['total_amt'].tolist())

    data = [trace0]
    fig = go.Figure(data=data,layout=go.Layout())
    fig.update_layout(height=400)
    return fig


@app.callback(Output('pie-customer-age','figure'),
              Input('age-slider','value'))
def tab3_customer_age(value):
    customers_df = df.merged
    customers_df = tab3.prepare_date_customers(customers_df)
    customers_df = customers_df[(customers_df['age'] >= value[0]) & (customers_df['age'] <= value[1])]
    customers_df = customers_df.groupby(['Store_type'])['total_amt'].sum().reset_index()

    fig = go.Figure(data=[go.Pie(labels=customers_df['Store_type'],values=customers_df['total_amt'])])
    fig.update_layout(height=400)
    return fig


if __name__ == '__main__':
    app.run(debug=True)
