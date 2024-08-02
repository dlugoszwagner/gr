import streamlit as st
import pandas as pd
from pathlib import Path
import locale
import os

# Definindo a localização para formatação
if os.name == 'nt':  # Se o sistema operacional for Windows
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
else:  # Para outros sistemas operacionais
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
        usecols=['NUMERO', 'CODIGO', 'VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']
    )
    df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']] = df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']].replace(',', '.', regex=True).astype(float)
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
    merged_df[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']] = merged_df[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']].fillna(0)
    return merged_df

# Função para fazer o merge dos dataframes de vendas e custo
def merge_custo(df_vendas, df_tabelacusto):
    joined_df = pd.merge(df_vendas, df_tabelacusto, on='CODPRODUTO', how='left')
    joined_df['VALOR_TOTAL_CUSTO'] = joined_df['UNI'] * joined_df['VALORCUSTO']
    joined_df['VALOR_TOTAL_CUSTO'] = joined_df['VALOR_TOTAL_CUSTO'].fillna(0)  # Preencher valores NaN com 0
    return joined_df

# Função para formatar valores em milhares sem casas decimais
def formatar_milhar(valor):
    return locale.format_string('%d', valor, grouping=True)

# Lendo os dados
df_vendas = ler_vendas()
df_tabelacusto = ler_custo()
df_impostos = ler_impostos()

# Convertendo as colunas CODPRODUTO e CODNOTAFISCAL para string
df_vendas['CODPRODUTO'] = df_vendas['CODPRODUTO'].astype(str)
df_vendas['CODNOTAFISCAL'] = df_vendas['CODNOTAFISCAL'].astype(str)
df_tabelacusto['CODPRODUTO'] = df_tabelacusto['CODPRODUTO'].astype(str)
df_impostos['CODIGO'] = df_impostos['CODIGO'].astype(str)
df_impostos['NUMERO'] = df_impostos['NUMERO'].astype(str)

# Convertendo colunas para tipos numéricos
df_vendas['UNI'] = pd.to_numeric(df_vendas['UNI'], errors='coerce')
df_vendas['VALOR'] = pd.to_numeric(df_vendas['VALOR'], errors='coerce')
df_tabelacusto['VALORCUSTO'] = pd.to_numeric(df_tabelacusto['VALORCUSTO'], errors='coerce')
df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']] = df_impostos[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']].apply(pd.to_numeric, errors='coerce')

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
joined_custo['TOTALIMPOSTOS'] = joined_custo[['VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST']].sum(axis=1)

# Criar a coluna FATURAMENTOLIQ
joined_custo['FATURAMENTOLIQ'] = joined_custo['VALOR'] - joined_custo['TOTALIMPOSTOS']

# Criar a coluna MC
joined_custo['MC'] = joined_custo['FATURAMENTOLIQ'] - joined_custo['VALOR_TOTAL_CUSTO']

# Agrupar por vendedor e somar as colunas necessárias
agrupar_vendedor = joined_custo.groupby('NOMEVENDEDOR')[['VALOR', 'VALORICMS', 'VALORIPI', 'VALORPIS', 'VALORCOFINS', 'VALORICMSST', 'TOTALIMPOSTOS', 'VALOR_TOTAL_CUSTO', 'FATURAMENTOLIQ', 'MC']].sum()

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
    'FATURAMENTOLIQ': 'FATURAMENTO LIQ',
    'VALOR_TOTAL_CUSTO': 'CUSTO PRODUTO',
    'MC': 'MC',
    'TOTALIMPOSTOS': 'TOTAL IMPOSTOS'
})

# Reordenar colunas
agrupar_vendedor = agrupar_vendedor[['FATURAMENTO', 'ICMS', 'IPI', 'PIS', 'COFINS', 'ICMSST', 'TOTAL IMPOSTOS', 'FATURAMENTO LIQ', 'CUSTO PRODUTO', 'MC', 'PORCENTAGEM']]

# Adicionar linha de totais
totals = agrupar_vendedor[['FATURAMENTO', 'ICMS', 'IPI', 'PIS', 'COFINS', 'ICMSST', 'TOTAL IMPOSTOS', 'FATURAMENTO LIQ', 'CUSTO PRODUTO', 'MC']].sum()
totals['PORCENTAGEM'] = (totals['MC'] / totals['FATURAMENTO LIQ']) * 100
totals = pd.DataFrame(totals).T
totals.index = ['TOTAL']
agrupar_vendedor = pd.concat([agrupar_vendedor, totals])

# Formatar e exibir o DataFrame
df_styled = agrupar_vendedor.style.format({
    'FATURAMENTO': lambda x: f'R$ {formatar_milhar(x)}',
    'ICMS': lambda x: f'R$ {formatar_milhar(x)}',
    'IPI': lambda x: f'R$ {formatar_milhar(x)}',
    'PIS': lambda x: f'R$ {formatar_milhar(x)}',
    'COFINS': lambda x: f'R$ {formatar_milhar(x)}',
    'ICMSST': lambda x: f'R$ {formatar_milhar(x)}',
    'TOTAL IMPOSTOS': lambda x: f'R$ {formatar_milhar(x)}',
    'FATURAMENTO LIQ': lambda x: f'R$ {formatar_milhar(x)}',
    'CUSTO PRODUTO': lambda x: f'R$ {formatar_milhar(x)}',
    'MC': lambda x: f'R$ {formatar_milhar(x)}', 
    'PORCENTAGEM': '{:.2f}%'
}).set_properties(**{'width': '120px'})

st.write(df_styled)

# Adicionar seleção de vendedor
vendedores = ['Todos'] + agrupar_vendedor.index[:-1].tolist()  # Adiciona 'Todos' na lista de vendedores
vendedor_selecionado = st.selectbox('Selecione o Vendedor para detalhes:', vendedores)

# Filtrar detalhes das vendas para o vendedor selecionado
if vendedor_selecionado and vendedor_selecionado != 'Todos':
    detalhes_vendas = df_vendas_fil[df_vendas_fil['NOMEVENDEDOR'] == vendedor_selecionado]
else:
    detalhes_vendas = df_vendas_fil

# Agrupar por DESCPRODUTO
detalhes_agregados = detalhes_vendas.groupby('DESCPRODUTO').agg({
    'UNI': 'sum',
    'VALOR': 'sum'
}).reset_index()

# Adicionar linha de totais
totals = detalhes_agregados[['UNI', 'VALOR']].sum()
totals['DESCPRODUTO'] = 'TOTAL GERAL'

# Criar um DataFrame para a linha de totais
totals_df = pd.DataFrame([totals])

# Concatenar com o DataFrame existente
detalhes_agregados = pd.concat([detalhes_agregados, totals_df], ignore_index=True)

# Exibindo detalhes agregados com linha de totais
st.write('**Detalhes Agregados por Produto**')
st.dataframe(detalhes_agregados.style.format({
    'VALOR': lambda x: f'R$ {formatar_milhar(x)}',
    'UNI': '{:.0f}',
}))