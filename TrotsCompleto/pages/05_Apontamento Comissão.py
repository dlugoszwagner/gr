import streamlit as st
import pandas as pd
from pathlib import Path

# Caminho para os arquivos CSV
pasta_datasets = Path(__file__).parent.parent / 'datasets'

# Carregar dados iniciais
comissoes_df = pd.read_csv(
    pasta_datasets / 'comissoes.csv', 
    encoding='latin-1', 
    sep=';'
)

representantes_df = pd.read_csv(
    pasta_datasets / 'representante.csv', 
    encoding='latin-1', 
    sep=';'
)

# Função para gerar próximo ID
def proximo_id():
    if 'ID' in comissoes_df.columns and not comissoes_df.empty:
        return max(comissoes_df['ID'], default=0) + 1
    else:
        return 1  # Caso a coluna 'ID' não exista ou o DataFrame esteja vazio

# Interface do CRUD
st.title('Comissões')

# Formulário para adicionar nova comissão
st.subheader('Adicionar Nova Comissão')
id_novo = proximo_id()
data_nova = st.date_input('Data da Comissão')
mes_novo = data_nova.month  # Extrai o mês da data selecionada automaticamente

# Lista de opções para seleção do código e nome do vendedor
opcoes_vendedores = [(row['CODVENDEDOR'], f"{row['CODVENDEDOR']} - {row['NOMEVENDEDOR']}") for index, row in representantes_df.iterrows()]

# Seleção do vendedor
codvendedor_selecionado = st.selectbox('Selecione o Vendedor', options=opcoes_vendedores, format_func=lambda x: x[1])

# Extrai apenas o código do vendedor selecionado
codvendedor_selecionado = codvendedor_selecionado[0]

# Campo para digitar o valor da comissão
valor_comissao = st.number_input('Valor da Comissão', min_value=0.0)

# Botão para adicionar
if st.button('Adicionar'):
    # Criando um novo DataFrame para adicionar a nova comissão
    nova_comissao = pd.DataFrame({
        'ID': [id_novo],
        'DATA': [data_nova.strftime('%Y-%m-%d')],
        'MES': [mes_novo],
        'CODVENDEDOR': [codvendedor_selecionado],
        'NOMEVENDEDOR': [representantes_df.loc[representantes_df['CODVENDEDOR'] == codvendedor_selecionado, 'NOMEVENDEDOR'].values[0]],
        'VALORCOMISSAO': [valor_comissao]
    })
    
    # Concatenando o novo DataFrame com o DataFrame original
    comissoes_df = pd.concat([comissoes_df, nova_comissao], ignore_index=True)
    
    # Salvando o DataFrame atualizado de volta no arquivo CSV com separador ponto e vírgula
    comissoes_df.to_csv(pasta_datasets / 'comissoes.csv', index=False, sep=';')
    
    # Mensagem de sucesso
    st.success('Comissão adicionada com sucesso.')

# Mostrar tabela de comissões
st.subheader('Lista de Comissões')
st.write(comissoes_df)
