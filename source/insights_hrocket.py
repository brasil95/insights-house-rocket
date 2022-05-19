# -*- coding: utf-8 -*-
"""
Created on Fri May 13 16:56:40 2022

@author: vbras
"""
# ------------------------------------------
# Libraries
# ------------------------------------------
import geopandas
import streamlit as st
import pandas    as pd
pd.set_option('display.float_format',  '{:,.2f}'.format)
import numpy     as np
import folium
import seaborn as sns
import matplotlib.pyplot as plt

from datetime import datetime, time

from streamlit_folium import folium_static
from folium.plugins   import MarkerCluster

import plotly.express as px

from mypackage import regras_negocios

# ------------------------------------------
# Settings
# ------------------------------------------
st.set_page_config( layout='wide' )

# ------------------------------------------
# Helper Functions
# ------------------------------------------
@st.cache(allow_output_mutation=True)
def get_data(path):
    data = pd.read_csv(path)

    return data


@st.cache(allow_output_mutation=True)
def get_geofile(url):
    geofile = geopandas.read_file(url)

    return geofile


def set_attributes(data):    
    data.drop_duplicates(subset='id', keep="last", inplace=True)
    data.drop(data[data['bedrooms'] == 33].index, inplace=True)
    data.drop(data[data['price'] >= 1000000].index, inplace=True)

    data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
    data['yr_built'] = pd.to_datetime(data['yr_built'], format='%Y')
    data['yr_renovated'] = data['yr_renovated'].apply(lambda x: np.nan if x == 0 else pd.to_datetime(x, format='%Y'))

    return data


def data_overview(data):
    st.sidebar.title( 'Filtro dos dados' )
    f_attributes = st.sidebar.multiselect('Insira as colunas', data.columns) 
    f_zipcode = st.sidebar.multiselect( 
        'Insira o zipcode', 
        data['zipcode'].unique())

    st.title('Overview dos Dados')
    st.header('Base de dados')

    if (f_zipcode != [] ) & ( f_attributes != []):
        data = data.loc[data['zipcode'].isin(f_zipcode), f_attributes]

    elif (f_zipcode != []) & (f_attributes == []):
        data = data.loc[data['zipcode'].isin(f_zipcode), :]

    elif (f_zipcode == []) & (f_attributes != []):
        data = data.loc[:, f_attributes]

    else:
        data = data.copy()

    st.dataframe(data)
 

    # Estatística descritiva
    cat_vars = ['bedrooms', 'bathrooms', 'floors', 'waterfront', 'view', 
            'condition', 'grade']

    num_vars = ['date', 'sqft_living', 'sqft_lot', 'sqft_above', 'sqft_basement', 
            'yr_built', 'yr_renovated', 'sqft_living15', 'sqft_lot15', 'price']

    num_attributes = data[num_vars]

    df1 = num_attributes.describe().transpose().reset_index()[['index', 'max', 'min', 'mean', '50%', 'std']]
    df1.columns = ['atributos', 'max', 'min', 'mean', 'median', 'std'] 
    
    st.header( 'Estatísticas descritivas' )
    st.dataframe( df1 )    

    # Histograma do preço
    fig = plt.figure(figsize=(7, 3))
    sns.histplot(data = data['price'], color = 'indianred')
    st.header( 'Histograma do preço' )
    st.pyplot(fig)

    # Gráficos de dispersão das variáveis em relação ao preço
    st.header('Gráficos de dispersão das variáveis númericas em relação ao preço')
    fig = plt.figure(figsize = (20,40 ))

    x = 1
    for d in data[num_vars]:
        plt.subplot(9, 3, x)
        sns.scatterplot(data = data[num_vars], x = d, y = 'price', color = 'indianred')
        x += 1

    st.pyplot(fig)

    # Gráficos boxplots das variáveis em relação ao preço
    st.header('Gráficos boxplots das variáveis categóricas em relação ao preço')
    fig = plt.figure(figsize = (20,40 ))

    x = 1
    for d in data[cat_vars]:
        plt.subplot(9, 3, x)
        sns.boxplot(data = data, x = d, y = 'price', palette = 'flare')
        x += 1

    st.pyplot(fig)

    return None

def region_overview(data, geofile):
    st.title('Overview da Região dos Imóveis')

    c1, c2 = st.columns(( 1, 1 ))
    c1.header('Densidade do Portfólio')


    df = data.copy()

    # Base Map - Folium 
    density_map = folium.Map(location=[data['lat'].mean(), 
                            data['long'].mean() ],
                            default_zoom_start=15) 

    marker_cluster = MarkerCluster().add_to(density_map)
    for name, row in df.iterrows():
        folium.Marker([row['lat'], row['long']], 
            popup='Sold R${0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, year built: {5}'.format( 
                                        row['price'],
                                        row['date'],
                                        row['sqft_living'],
                                        row['bedrooms'],
                                        row['bathrooms'],
                                        row['yr_built'] )).add_to(marker_cluster)


    with c1:
        folium_static(density_map)


    # Region Price Map
    c2.header('Densidade dos Preços')

    df = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
    df.columns = ['zip', 'price']

    #df = df.sample(10)

    geofile = geofile[geofile['ZIP'].isin(df['zip'].tolist())]

    region_price_map = folium.Map(location=[data['lat'].mean(), 
                                data['long'].mean() ],
                                default_zoom_start=15) 


    folium.Choropleth(data = df,
                                geo_data = geofile,
                                columns=['zip', 'price'],
                                key_on='feature.properties.ZIP',
                                fill_color='YlOrRd',
                                fill_opacity = 0.7,
                                line_opacity = 0.2,
                                legend_name='preço médio').add_to(region_price_map)

    with c2:
        folium_static(region_price_map)

    return None

def set_insights(data):
    st.title('Top 3 Insights')

    st.header('1. Imóveis com vista para água são 40% mais caros na média.')
    fig = plt.figure(figsize=(7, 3)) 

    sns.boxplot(data = data[['waterfront', 'price']],
            x = 'waterfront', y = 'price', palette = 'flare')

    plt.title('Boxplot - Waterfront' )
    sns.despine(bottom = True, left = True)
    st.pyplot(fig)

    st.header('2. Imóveis com condition acima ou igual a 3 são 53% mais caros na média.')
    fig = plt.figure(figsize=(7, 3)) 

    sns.boxplot(data = data[['condition', 'price']],
            x = 'condition', y = 'price', palette = 'flare')

    plt.title('Boxplot - Condition' )
    sns.despine(bottom = True, left = True)
    st.pyplot(fig)

    st.header('3. Imóveis com grade acima de 7 são 67% mais caros na média.')
    fig = plt.figure(figsize=(7, 3)) 

    sns.boxplot(data = data[['grade', 'price']],
            x = 'grade', y = 'price', palette = 'flare')

    plt.title('Boxplot - Grade' )
    sns.despine(bottom = True, left = True)
    st.pyplot(fig)

    return None

def set_report(data):
    st.sidebar.title( 'Sugestões de negócios' )
    st.title( 'Preço de compra e venda' )

    # Mediana do zipcode
    df_columns = data[["id", "zipcode", "condition", "waterfront", "grade", "sqft_living","price"]].copy()

    median_zipcode = df_columns.groupby("zipcode")[["price", "sqft_living"]].median().reset_index(drop=False)

    df_median = pd.merge(df_columns, median_zipcode, on="zipcode", how="left", suffixes=["", "_median"])

    # Aplicando função das regras de negócio de compra
    df_median["status_compra"] = df_median.apply(regras_negocios.status_compra, axis=1)  

    # Criando faixa inferior e superior a mediana
    param_inf = 0.90
    param_sup = 1.10
    df_median["faixa_inf"] = df_median["price_median"] * param_inf
    df_median["faixa_sup"] = df_median["price_median"] * param_sup

    # Aplicando função para definir faixa atual do imóvel
    df_median["faixa_atual"] = df_median.apply(regras_negocios.faixa_atual, axis=1)

    # Aplicando função para definir preço de venda
    df_median["preco_venda"] = df_median.apply(regras_negocios.preco_venda, axis=1)

    # Aplicando função para ajustar preços
    df_median["preco_venda"] = df_median.apply(regras_negocios.preco_ajuste, axis=1)

    # Definindo lucro de cada negócio
    df_median["oportunidade_lucro"] = df_median["preco_venda"] - df_median["price"]

    # Display relatório com as colunas necessárias
    cols_display = ['id', 'zipcode', 'condition', 
                    'waterfront', 'grade', 'sqft_living', 'price',
                    'price_median', 'status_compra', 'preco_venda', 'oportunidade_lucro']

    df = df_median[cols_display].copy()

    df = df[df["status_compra"] == "Comprar"].sort_values("oportunidade_lucro", ascending=False).reset_index(drop=True)

    st.dataframe(df)

    lucro = (df["oportunidade_lucro"].sum()/1000000).round(1)

    st.write('A oportunidade de lucro é de: $', lucro, 'MM')

    return None

if __name__ == "__main__":
    # ETL
    path = './inputs_heroku/kc_house_data.csv'
    url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'

    # load data
    data = get_data(path)
    geofile = get_geofile(url)

    # transform data
    data = set_attributes(data)

    data_overview(data)

    region_overview(data, geofile)

    set_insights(data)
    
    set_report(data)