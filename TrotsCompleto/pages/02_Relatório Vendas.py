from pathlib import Path
import streamlit as st
import pandas as pd
import locale

# Definição do caminho para o arquivo CSV
pasta_datasets = Path(__file__).parent.parent / 'datasets'
csv_file = pasta_datasets / 'sale.csv'  # Especifique o arquivo CSV aqui

# Função para carregar e ler o arquivo CSV
def load_csv(file):
    try:
        df = pd.read_csv(file, encoding='latin-1', parse_dates=True, sep=';')
        df['VALOR'] = df['VALOR'].astype(float)  # Convertendo VALOR para float
        return df
    except FileNotFoundError:
        st.error("Arquivo CSV não encontrado.")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return None

# Função para formatação de valores monetários
def currency_formatter(value):
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        st.error("Localidade 'pt_BR.UTF-8' não está disponível.")
        return value
    return '{:,.2f} R$'.format(value).replace(',', 'X').replace('.', ',').replace('X', '.')

# Carregar o CSV especificado
df = load_csv(csv_file)

if df is not None:
    st.write("### Relatório Venda > Filtragem e Análise de Dados")

    # Seleção de filtros dinâmicos
    filter_columns = st.multiselect("Selecione as colunas para filtrar", df.columns.tolist())

    for col in filter_columns:
        unique_values = ["Todos"] + df[col].dropna().unique().tolist()
        selected_value = st.selectbox(f'Selecione o valor para {col}', unique_values)

         # Armazenar o valor selecionado no estado
        st.session_state['filter_values'][col] = selected_value

        if selected_value != "Todos":
            df = df[df[col] == selected_value]

    # Atualizar o estado das colunas de filtro selecionadas
    st.session_state['filter_columns'] = filter_columns


    # Seleção das linhas e colunas para a tabela dinâmica
    rows = st.multiselect('Selecione as linhas', df.columns.tolist())
    columns = st.multiselect('Selecione as colunas', df.columns.tolist())

    if st.button('Gerar'):
        try:
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
    st.info("Por favor, verifique o arquivo CSV especificado.")
