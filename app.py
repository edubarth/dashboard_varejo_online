import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configurações da Página --- #
st.set_page_config(layout='wide', page_title='Dashboard de Vendas Online', page_icon='📈')

# --- Carregamento e Pré-processamento dos Dados --- #
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Online_Retail.csv', encoding='ISO-8859-1')
    except FileNotFoundError:
        st.error('O arquivo Online_Retail.csv não foi encontrado. Certifique-se de que ele está no mesmo diretório do app.py.')
        st.stop()

    # Tratamento de valores nulos e conversão de tipos
    df['Description'].fillna('Unknown', inplace=True)
    df.dropna(subset=['CustomerID'], inplace=True)
    df['CustomerID'] = df['CustomerID'].astype(int)
    
    # Tentativa de inferir o formato da data para maior robustez
    try:
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], format='%m/%d/%y %H:%M')
    except ValueError:
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
        st.warning('Alguns valores de data não puderam ser convertidos com o formato esperado e foram tratados como NaT.')
        df.dropna(subset=['InvoiceDate'], inplace=True) # Remover linhas com datas inválidas

    # Calcular Faturamento Final (Total Price)
    df['Faturamento Final'] = df['Quantity'] * df['UnitPrice']

    # Remover transações com quantidade ou preço unitário negativo/zero (devoluções/ajustes)
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0]
    
    return df

df = load_data()

# --- Título do Dashboard --- #
st.title('📈 Dashboard de Vendas Online')

# --- Sidebar para Filtros --- #
st.sidebar.header('Filtros')

# Filtro por País
paises_unicos = sorted(df['Country'].unique().tolist())
paises_selecionados = st.sidebar.multiselect(
    'Selecione o País',
    options=paises_unicos,
    default=paises_unicos # Seleciona todos por padrão
)

# Aplicar filtro de país
df_filtrado = df[df['Country'].isin(paises_selecionados)]

# Slider para filtrar por data (opcional, adicionei para exemplo)
min_date = df_filtrado['InvoiceDate'].min().to_pydatetime()
max_date = df_filtrado['InvoiceDate'].max().to_pydatetime()
date_range = st.sidebar.date_input(
    'Selecione o Intervalo de Datas',
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtrado = df_filtrado[(df_filtrado['InvoiceDate'].dt.date >= start_date) & (df_filtrado['InvoiceDate'].dt.date <= end_date)]
elif len(date_range) == 1:
    start_date = date_range[0]
    df_filtrado = df_filtrado[df_filtrado['InvoiceDate'].dt.date >= start_date]


# --- Indicador de Faturamento Total --- #
total_faturamento = df_filtrado['Faturamento Final'].sum()
st.markdown(f"""
    <div style="background-color:#add8e6; padding: 10px; border-radius: 5px; text-align: center;">
        <h3>Faturamento Total Selecionado: <span style="color:#28a745;">R$ {total_faturamento:,.2f}</span></h3>
    </div>
    <br>
    """, unsafe_allow_html=True)

# --- Gráficos Principais --- #

# 1. Tendência de Vendas Mensais
st.subheader('Tendência de Vendas Mensais')
monthly_sales = df_filtrado.set_index('InvoiceDate')['Faturamento Final'].resample('M').sum().reset_index()
monthly_sales['InvoiceDate'] = monthly_sales['InvoiceDate'].dt.strftime('%Y-%m') # Formato para exibição

fig_trend = px.line(
    monthly_sales,
    x='InvoiceDate',
    y='Faturamento Final',
    title='Faturamento Mensal Total (USD)',
    labels={'InvoiceDate': 'Mês', 'Faturamento Final': 'Faturamento (USD)'},
    markers=True
)
st.plotly_chart(fig_trend, use_container_width=True)

# Colunas para organizar os gráficos de Top Produtos
col1, col2 = st.columns(2)

with col1:
    # 2. Top 10 Produtos por Faturamento
    st.subheader('Top 10 Produtos por Faturamento')
    top_produtos_valor = df_filtrado.groupby('Description')['Faturamento Final'].sum().nlargest(10).reset_index()
    fig_top_valor = px.bar(
        top_produtos_valor,
        x='Faturamento Final',
        y='Description',
        orientation='h',
        title='Top 10 Produtos com Maior Faturamento',
        labels={'Faturamento Final': 'Faturamento (USD)', 'Description': 'Produto'},
        color='Faturamento Final', # Adiciona cor baseada no valor
        color_continuous_scale=px.colors.sequential.Viridis # Escala de cores
    )
    fig_top_valor.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_valor, use_container_width=True)

with col2:
    # 3. Top 10 Produtos por Quantidade
    st.subheader('Top 10 Produtos por Quantidade')
    top_produtos_quantidade = df_filtrado.groupby('Description')['Quantity'].sum().nlargest(10).reset_index()
    fig_top_quantidade = px.bar(
        top_produtos_quantidade,
        x='Quantity',
        y='Description',
        orientation='h',
        title='Top 10 Produtos com Maior Quantidade Vendida',
        labels={'Quantity': 'Quantidade Vendida', 'Description': 'Produto'},
        color='Quantity',
        color_continuous_scale=px.colors.sequential.Plasma
    )
    fig_top_quantidade.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_quantidade, use_container_width=True)

# 4. Faturamento por País (Top 10)
st.subheader('Faturamento por País (Top 10)')
faturamento_pais = df_filtrado.groupby('Country')['Faturamento Final'].sum().nlargest(10).reset_index()
fig_faturamento_pais = px.bar(
    faturamento_pais,
    x='Country',
    y='Faturamento Final',
    title='Faturamento Total por País',
    labels={'Country': 'País', 'Faturamento Final': 'Faturamento (USD)'},
    color='Faturamento Final',
    color_continuous_scale=px.colors.sequential.RdBu # Outra escala de cor
)
st.plotly_chart(fig_faturamento_pais, use_container_width=True)

# 5. Scatter Plot: Quantidade vs. Preço Unitário (para detecção de outliers)
st.subheader('Dispersão: Quantidade vs. Preço Unitário')
fig_scatter = px.scatter(
    df_filtrado,
    x='UnitPrice',
    y='Quantity',
    log_x=True, # Usar escala logarítmica para UnitPrice para melhor visualização de grandes variações
    log_y=True, # Usar escala logarítmica para Quantity
    hover_data=['Description', 'Faturamento Final'],
    title='Quantidade vs. Preço Unitário (Escala Logarítmica)',
    labels={'UnitPrice': 'Preço Unitário (USD, Log)', 'Quantity': 'Quantidade (Log)'}
)
st.plotly_chart(fig_scatter, use_container_width=True)
