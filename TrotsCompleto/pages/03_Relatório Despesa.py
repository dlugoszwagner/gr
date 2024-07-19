from pathlib import Path
import streamlit as st
import pandas as pd
import locale

# Definição do caminho para os arquivos CSV
pasta_datasets = Path(__file__).parent.parent / 'datasets'
csv_file_contas_a_pagar = pasta_datasets / 'contas_a_pagar.csv'
csv_file_contas = pasta_datasets / 'contas.csv'

# Função para carregar e ler os arquivos CSV
def load_csv(file):
    if not file.exists():
        st.error("Arquivo CSV não encontrado.")
        return None
    try:
        df = pd.read_csv(file, encoding='latin-1', parse_dates=True, sep=';')
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return None

# Função para converter string de valor monetário brasileiro para float
def br_to_float(value):
    try:
        return float(value.replace('.', '').replace(',', '.'))
    except ValueError:
        return value

# Função para formatação de valores monetários
def currency_formatter(value):
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        return value  # Retorna o valor sem formatação se a localidade não estiver disponível
    return '{:,.2f} R$'.format(value).replace(',', 'X').replace('.', ',').replace('X', '.')

# Carregar os CSVs especificados
df_contas_a_pagar = load_csv(csv_file_contas_a_pagar)
df_contas = load_csv(csv_file_contas)

if df_contas_a_pagar is not None and df_contas is not None:
    # Converter a coluna 'VALOR' para float
    df_contas_a_pagar['VALOR'] = df_contas_a_pagar['VALOR'].apply(br_to_float)
    
    # Realizar a junção dos dados usando a coluna 'COD'
    df = pd.merge(df_contas_a_pagar, df_contas, on='COD', how='left')
    
    st.write("### Relatório Despesa > Filtragem e Análise de Dados")

    # Inicialização do estado dos filtros
    if 'filter_columns' not in st.session_state:
        st.session_state['filter_columns'] = []
    if 'filter_values' not in st.session_state:
        st.session_state['filter_values'] = {}

    # Seleção de filtros dinâmicos
    filter_columns = st.multiselect("Selecione as colunas para filtrar", df.columns.tolist(), default=st.session_state['filter_columns'])

    for col in filter_columns:
        if col not in st.session_state['filter_values']:
            st.session_state['filter_values'][col] = "Todos"
        unique_values = ["Todos"] + df[col].dropna().unique().tolist()
        selected_value = st.selectbox(f'Selecione o valor para {col}', unique_values, index=unique_values.index(st.session_state['filter_values'][col]))

        # Armazenar o valor selecionado no estado
        st.session_state['filter_values'][col] = selected_value

        if selected_value != "Todos":
            df = df[df[col] == selected_value]

    # Atualizar o estado das colunas de filtro selecionadas
    st.session_state['filter_columns'] = filter_columns

    # Seleção das linhas e colunas para a tabela dinâmica
    if 'rows' not in st.session_state:
        st.session_state['rows'] = []
    if 'columns' not in st.session_state:
        st.session_state['columns'] = []

    rows = st.multiselect('Selecione as linhas', df.columns.tolist(), default=st.session_state['rows'])
    columns = st.multiselect('Selecione as colunas', df.columns.tolist(), default=st.session_state['columns'])

    if st.button('Gerar'):
        try:
            # Armazenar as linhas e colunas selecionadas no estado
            st.session_state['rows'] = rows
            st.session_state['columns'] = columns

            pivot_table = pd.pivot_table(df, values='VALOR', index=rows, columns=columns, aggfunc='sum')
            
            # Adicionar uma linha com os totais
            total_row = pivot_table.sum(numeric_only=True).to_frame().T
            total_row.index = ['Total']
            pivot_table = pd.concat([pivot_table, total_row])

            # Aplicar formatação aos valores na tabela dinâmica
            pivot_table = pivot_table.applymap(currency_formatter)
            
            st.write("### Tabela Dinâmica Gerada")
            st.dataframe(pivot_table)
        except Exception as e:
            st.error(f"Erro ao gerar a tabela dinâmica: {e}")
else:
    st.info("Por favor, verifique os arquivos CSV especificados.")
