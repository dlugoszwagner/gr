import streamlit as st
import pandas as pd
from pathlib import Path
import locale

# Definindo a localização para formatação
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Caminho para os datasets
pasta_datasets = Path(__file__).parent.parent / 'datasets'

# Função para ler o arquivo CSV de vendas
def ler_vendas():
    return pd.read_csv(
        pasta_datasets / 'sale.csv', 
        encoding='latin-1', 
        parse_dates=True, 
        sep=';', 
        usecols=['ANOVENDA', 'MESVENDA', 'TIPOVENDA', 'NOMEVENDEDOR', 'CODPRODUTO', 'DESCPRODUTO', 'UNI', 'VALOR', 'CODNOTAFISCAL']
    )

# Função para ler o arquivo CSV de custo
def ler_custo():
    df = pd.read_csv(
        pasta_datasets / 'custoprod.csv', 
        encoding='latin-1', 
        parse_dates=True, 
        sep=';', 
        usecols=['CODPRODUTO', 'DESCPRODUTO', 'VALORCUSTO']
    )
    df['VALORCUSTO'] = df['VALORCUSTO'].str.replace(',', '.').replace('\\N', 'NaN')
    df['VALORCUSTO'] = pd.to_numeric(df['VALORCUSTO'], errors='coerce')
    return df

# Função para ler o arquivo CSV de impostos
def ler_impostos():
    df_impostos = pd.read_csv(
        pasta_datasets / 'impostos.csv', 
        encoding='latin-1', 
        parse_dates=True, 
        sep=';', 
        usecols=['NUMERO', 'CODIGO', 'VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']
    )
    df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']] = df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']].replace(',', '.', regex=True).astype(float)
    return df_impostos

# Função para filtrar vendas
def filtrar_vendas(df):
    df_fil = df.query("TIPOVENDA in ['Pronta Entrega', 'Venda a Vista', 'Venda a Prazo']")
    df_fil['UNI'] = pd.to_numeric(df_fil['UNI'], errors='coerce').fillna(0).astype(int)
    return df_fil

# Função para fazer o merge dos dataframes de vendas e impostos
def merge_vendas_impostos(df_vendas, df_impostos):
    merged_df = pd.merge(
        df_vendas, 
        df_impostos, 
        left_on=['CODNOTAFISCAL', 'CODPRODUTO'], 
        right_on=['NUMERO', 'CODIGO'], 
        how='left'
    )
    merged_df[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']] = merged_df[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']].fillna(0)
    return merged_df

# Função para fazer o merge dos dataframes de vendas e custo
def merge_custo(df_vendas, df_tabelacusto):
    joined_df = pd.merge(df_vendas, df_tabelacusto, on='CODPRODUTO', how='left')
    joined_df['VALOR_TOTAL_CUSTO'] = joined_df['UNI'] * joined_df['VALORCUSTO']
    return joined_df

# Função para formatar valores em milhares
def formatar_milhar(valor):
    return locale.format_string('%.2f', valor, grouping=True)

# Lendo os dados
df_vendas = ler_vendas()
df_tabelacusto = ler_custo()
df_impostos = ler_impostos()

# Convertendo as colunas CODPRODUTO e CODNOTAFISCAL para string em ambos os DataFrames
df_vendas['CODPRODUTO'] = df_vendas['CODPRODUTO'].astype(str)
df_vendas['CODNOTAFISCAL'] = df_vendas['CODNOTAFISCAL'].astype(str)
df_tabelacusto['CODPRODUTO'] = df_tabelacusto['CODPRODUTO'].astype(str)
df_impostos['CODIGO'] = df_impostos['CODIGO'].astype(str)
df_impostos['NUMERO'] = df_impostos['NUMERO'].astype(str)

# Filtrando os dados de vendas
df_vendas_fil = filtrar_vendas(df_vendas)

# Filtros de ANOVENDA e MESVENDA
anos = df_vendas_fil['ANOVENDA'].unique()
meses = df_vendas_fil['MESVENDA'].unique()

ano_selecionado = st.multiselect('Selecione o(s) Ano(s) de Venda:', anos)
mes_selecionado = st.multiselect('Selecione o(s) Mês(es) de Venda:', meses)

# Filtrar o DataFrame de vendas com base nas seleções
if ano_selecionado:
    df_vendas_fil = df_vendas_fil[df_vendas_fil['ANOVENDA'].isin(ano_selecionado)]

if mes_selecionado:
    df_vendas_fil = df_vendas_fil[df_vendas_fil['MESVENDA'].isin(mes_selecionado)]

# Executar a função de merge com o DataFrame filtrado e os impostos
joined_vendas_impostos = merge_vendas_impostos(df_vendas_fil, df_impostos)

# Realizar o merge do DataFrame resultante com o DataFrame de custos
joined_custo = merge_custo(joined_vendas_impostos, df_tabelacusto)

# Criar a coluna TOTALIMPOSTOS
joined_custo['TOTALIMPOSTOS'] = joined_custo[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS']].sum(axis=1)

# Criar a coluna FATURAMENTOLIQ
joined_custo['FATURAMENTOLIQ'] = joined_custo['VALOR'] - joined_custo['TOTALIMPOSTOS']

# Criar a coluna MC
joined_custo['MC'] = joined_custo['FATURAMENTOLIQ'] - joined_custo['VALOR_TOTAL_CUSTO']

# Agrupar por vendedor e somar as colunas necessárias
agrupar_vendedor = joined_custo.groupby('NOMEVENDEDOR')[['VALOR', 'VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'DESCONTOS', 'TOTALIMPOSTOS', 'VALOR_TOTAL_CUSTO', 'FATURAMENTOLIQ', 'MC']].sum()

# Criar coluna de porcentagem
agrupar_vendedor['PORCENTAGEM'] = (agrupar_vendedor['MC'] / agrupar_vendedor['FATURAMENTOLIQ']) * 100

# Renomear colunas
agrupar_vendedor = agrupar_vendedor.rename(columns={
    'VALOR': 'FATURAMENTO',
    'VALORICMS': 'ICMS',
    'VALORIPI': 'IPI',
    'VALORPIS': 'PIS',
    'VALORCOFINS': 'COFINS',
    'VALORICMSST': 'ICMSST',
    'DESCONTOS': 'DESCONTOS',
    'FATURAMENTOLIQ': 'FATURAMENTO LIQ',
    'VALOR_TOTAL_CUSTO': 'CUSTO PRODUTO',
    'MC': 'MC',
    'TOTALIMPOSTOS': 'TOTAL IMPOSTOS'
})

# Reordenar colunas
agrupar_vendedor = agrupar_vendedor[['FATURAMENTO', 'ICMS', 'IPI', 'PIS', 'COFINS', 'ICMSST', 'DESCONTOS', 'TOTAL IMPOSTOS', 'FATURAMENTO LIQ', 'CUSTO PRODUTO', 'MC', 'PORCENTAGEM']]

# Adicionar linha de totais
totals = agrupar_vendedor[['FATURAMENTO', 'ICMS', 'IPI', 'PIS', 'COFINS', 'ICMSST', 'DESCONTOS', 'TOTAL IMPOSTOS', 'FATURAMENTO LIQ', 'CUSTO PRODUTO', 'MC']].sum()
totals['PORCENTAGEM'] = (totals['MC'] / totals['FATURAMENTO LIQ']) * 100
totals = pd.DataFrame(totals).T
totals.index = ['TOTAL']
agrupar_vendedor = pd.concat([agrupar_vendedor, totals])

# Destaque dos totais em colunas lado a lado com tamanho menor, 4 por linha
st.write("### Totais")
col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<h5>Faturamento</h5><p style='font-size:16px'>{formatar_milhar(totals['FATURAMENTO'][0])} R$</p>", unsafe_allow_html=True)
col2.markdown(f"<h5>ICMS</h5><p style='font-size:16px'>{formatar_milhar(totals['ICMS'][0])} R$</p>", unsafe_allow_html=True)
col3.markdown(f"<h5>IPI</h5><p style='font-size:16px'>{formatar_milhar(totals['IPI'][0])} R$</p>", unsafe_allow_html=True)
col4.markdown(f"<h5>PIS</h5><p style='font-size:16px'>{formatar_milhar(totals['PIS'][0])} R$</p>", unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)
col5.markdown(f"<h5>COFINS</h5><p style='font-size:16px'>{formatar_milhar(totals['COFINS'][0])} R$</p>", unsafe_allow_html=True)
col6.markdown(f"<h5>ICMSST</h5><p style='font-size:16px'>{formatar_milhar(totals['ICMSST'][0])} R$</p>", unsafe_allow_html=True)
col7.markdown(f"<h5>DESCONTOS</h5><p style='font-size:16px'>{formatar_milhar(totals['DESCONTOS'][0])} R$</p>", unsafe_allow_html=True)
col8.markdown(f"<h5>Total Impostos</h5><p style='font-size:16px'>{formatar_milhar(totals['TOTAL IMPOSTOS'][0])} R$</p>", unsafe_allow_html=True)

col9, col10, col11, col12 = st.columns(4)
col9.markdown(f"<h5>Custo Produto</h5><p style='font-size:16px'>{formatar_milhar(totals['CUSTO PRODUTO'][0])} R$</p>", unsafe_allow_html=True)
col10.markdown(f"<h5>Faturamento Líquido</h5><p style='font-size:16px'>{formatar_milhar(totals['FATURAMENTO LIQ'][0])} R$</p>", unsafe_allow_html=True)
col11.markdown(f"<h5>MC</h5><p style='font-size:16px'>{formatar_milhar(totals['MC'][0])} R$</p>", unsafe_allow_html=True)

col13 = st.columns(1)
col13[0].markdown(f"<h5>Margem %</h5><p style='font-size:16px'>{totals['PORCENTAGEM'][0]:.2f}%</p>", unsafe_allow_html=True)

# Formatar e exibir o DataFrame
df_styled = agrupar_vendedor.style.format({
    'FATURAMENTO': lambda x: formatar_milhar(x) + ' R$',
    'ICMS': lambda x: formatar_milhar(x) + ' R$',
    'IPI': lambda x: formatar_milhar(x) + ' R$',
    'PIS': lambda x: formatar_milhar(x) + ' R$',
    'COFINS': lambda x: formatar_milhar(x) + ' R$',
    'ICMSST': lambda x: formatar_milhar(x) + ' R$',
    'DESCONTOS': lambda x: formatar_milhar(x) + ' R$',
    'TOTAL IMPOSTOS': lambda x: formatar_milhar(x) + ' R$',
    'FATURAMENTO LIQ': lambda x: formatar_milhar(x) + ' R$',
    'CUSTO PRODUTO': lambda x: formatar_milhar(x) + ' R$',
    'MC': lambda x: formatar_milhar(x) + ' R$',
    'PORCENTAGEM': '{:.2f}%'
}).set_properties(**{'width': '120px'})

st.write(df_styled)
