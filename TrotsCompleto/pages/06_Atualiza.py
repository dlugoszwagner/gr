import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from pathlib import Path
import locale
import json
from datetime import datetime

# Tentando definir o locale
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error as e:
    st.error(f"Locale error: {e}")

# Caminho para os datasets
pasta_datasets = Path(__file__).parent / 'datasets'

# Função para conectar ao banco de dados MySQL
def conectar_mysql():
    try:
        connection = mysql.connector.connect(
             host='Servidor',
            database='comercio',
            user='Trots2303',
            password='Trots2303#2024',
            port=3306,
            charset='utf8'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return None

# Função para carregar a última data e hora de atualização
def carregar_ultima_atualizacao():
    path = Path(__file__).parent / 'ultima_atualizacao.json'
    if path.exists():
        try:
            with open(path, 'r') as f:
                ultima_atualizacao = json.load(f)
            return ultima_atualizacao.get('ultima_atualizacao')
        except (json.JSONDecodeError, KeyError):
            return None
    else:
        return None

# Função para salvar a data e hora da última atualização
def salvar_ultima_atualizacao(data_hora):
    path = Path(__file__).parent / 'ultima_atualizacao.json'
    with open(path, 'w') as f:
        json.dump({'ultima_atualizacao': data_hora}, f)

def carregar_csv():
    csv_path = Path(__file__).parent / 'dados_vendas.csv'
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, sep=',', on_bad_lines='skip', encoding='latin-1', engine='python')
            return df
        except pd.errors.ParserError as e:
            st.error(f"Erro ao analisar o CSV: {e}")
            return pd.DataFrame()
    else:
        # Se o arquivo não existir, crie um DataFrame vazio com as colunas necessárias
        colunas = ['CODPRODUTO', 'DESCPRODUTO', 'NroVenda', 'CODNOTAFISCAL', 'StatusNota', 'PedidoVendedor', 'CodCliente', 'CodVendedor', 
                   'NOMEVENDEDOR', 'TIPOVENDA', 'DataVenda', 'MESVENDA', 'ANOVENDA', 'HoraVenda', 'DataEntrega', 'NascimentoCliente', 
                   'CNPJCPF', 'FoneComercial', 'FoneCelular', 'NomeCliente', 'NomeFantasia', 'Endereco', 'Numero', 'Complemento', 
                   'Bairro', 'CEP', 'UF', 'Cidade', 'Status', 'DataStatus', 'HoraStatus', 'Placa', 'CodCondPagto', 'PesoLiquido', 
                   'QtdeVolumes', 'UNI', 'QtdeTotalMercDevolvidasVenda', 'VALOR', 'ValorDespesas', 'ValorFrete', 'ValorICMSST', 
                   'ValorIPI', 'PercentualDescontos', 'DATA_ATUALIZACAO']
        df = pd.DataFrame(columns=colunas)
        return df



# Função para consultar novos dados do banco de dados a partir de uma data específica
def consultar_dados_periodo(data_inicio, data_fim):
    try:
        connection = conectar_mysql()
        if connection.is_connected():
            query = """
            SELECT 
                produtos_acabados.pacodigo AS CODPRODUTO,
                produtos_acabados.padescricao AS DESCPRODUTO,
                NOTA_FISCAL01.NF01SEQUENCIA AS NroVenda,
                NOTA_FISCAL01.NF01NF AS CODNOTAFISCAL,
                CASE
                    WHEN NOTA_FISCAL01.NF01NF>1 THEN 'SIM'
                    ELSE 'NAO'
                END AS StatusNota,
                NOTA_FISCAL01.NF01PEDIDOVENDEDOR AS PedidoVendedor,
                NOTA_FISCAL01.CLIENCODIGO AS CodCliente,
                NOTA_FISCAL01.REPRCODIGO AS CodVendedor,
                REPRESENTANTES.REPRNOME AS NOMEVENDEDOR,
                NOTA_FISCAL01.NF01VENDAORCA AS TIPOVENDA,
                NOTA_FISCAL01.NF01DATA AS DataVenda,
                MONTH(NOTA_FISCAL01.NF01DATA) as MESVENDA,
                YEAR(NOTA_FISCAL01.NF01DATA) as ANOVENDA,
                NOTA_FISCAL01.NF01HORASAIDA AS HoraVenda,
                NOTA_FISCAL01.NF01ENTREGA AS DataEntrega,
                CLIENTES.CLIENNASCIMENTO AS NascimentoCliente,
                CLIENTES.CLIENCNPJCPF AS CNPJCPF,
                CLIENTES.CLIENFONECOMERCIAL AS FoneComercial,
                CLIENTES.CLIENFONECELULAR AS FoneCelular,
                IF(NOTA_FISCAL01.CLIENCODIGO = 1
                    AND IFNULL(NOTA_FISCAL01.NF01CLINOME, "") <> "", NOTA_FISCAL01.NF01CLINOME, CLIENTES.CLIENNOME) AS NomeCliente,
                IF(IFNULL(CLIENTES.CLIENFANTASIA, "") = "", CLIENTES.CLIENNOME, CLIENTES.CLIENFANTASIA) AS NomeFantasia,
                CLIENTES.CLIENENDERECO AS Endereco,
                CLIENTES.CLIENENDERECONUMERO AS Numero,
                CLIENTES.CLIENCOMPLEMENTO AS Complemento,
                CLIENTES.CLIENBAIRRO AS Bairro,
                CLIENTES.CLIENCEP AS CEP,
                CLIENTES.CLIENUF AS UF,
                CLIENTES.CLIENCIDADE AS Cidade,       
                NOTA_FISCAL01.NF01CONFERIDO AS Status,
                NOTA_FISCAL01.NF01DATASTATUS AS DataStatus,
                NOTA_FISCAL01.NF01HORASTATUS AS HoraStatus,
                NOTA_FISCAL01.NF01PLACA AS Placa,
                NOTA_FISCAL01.CPCODIGO AS CodCondPagto,
                (NOTA_FISCAL02.NF02QTDE/IFNULL(PRODUTOS_ACABADOS.PAPESO_VOLUME,1)) AS PesoLiquido,
                (NOTA_FISCAL02.NF02QTDE/IFNULL(PRODUTOS_ACABADOS.PAQTDE_VOLUMES,1)) AS QtdeVolumes,       
                SUM(IFNULL(NOTA_FISCAL02.NF02QTDE,0)) AS UNI,
                IFNULL(NOTA_FISCAL01.NF01QTDEMERCDEVOLVIDAS, 0) AS QtdeTotalMercDevolvidasVenda,
                SUM((ifnull(NOTA_FISCAL02.NF02VALOR,0)*ifnull(NOTA_FISCAL02.NF02QTDE,0))) AS VALOR,
                SUM((ifnull(NOTA_FISCAL01.NF01VLRDESPESAS,0)/ifnull(NOTA_FISCAL01.NF01PRODUTOSPEDIDO,0)*(ifnull(NOTA_FISCAL02.NF02VALOR,0)*ifnull(NOTA_FISCAL02.NF02QTDE,0)))) AS ValorDespesas,
                SUM((ifnull(NOTA_FISCAL01.NF01VLRFRETE,0)/ifnull(NOTA_FISCAL01.NF01PRODUTOSPEDIDO,0)*(ifnull(NOTA_FISCAL02.NF02VALOR,0)*ifnull(NOTA_FISCAL02.NF02QTDE,0)))) AS ValorFrete,
                SUM(ifnull(NOTA_FISCAL02.NF02VLRICMSST,0)) AS ValorICMSST,
                SUM(ifnull(NOTA_FISCAL02.NF02VALORIPI,0)) AS ValorIPI,
                GREATEST((ifnull(NOTA_FISCAL01.NF01VLRDESCONTO,0) / (ifnull(NOTA_FISCAL01.NF01PRODUTOSPEDIDO,0)-ifnull(NOTA_FISCAL01.NF01TOTMERCDEVOLVIDAS,0))),0)*100 AS PercentualDescontos,
                NOTA_FISCAL01.NF01DATA AS DATA_ATUALIZACAO
            FROM NOTA_FISCAL01
            LEFT JOIN NOTA_FISCAL02 ON NOTA_FISCAL01.NF01SEQUENCIA = NOTA_FISCAL02.NF01SEQUENCIA
            INNER JOIN CLIENTES ON NOTA_FISCAL01.CLIENCODIGO = CLIENTES.CLIENCODIGO
            LEFT JOIN PRODUTOS_ACABADOS ON NOTA_FISCAL02.PACODIGO = PRODUTOS_ACABADOS.PACODIGO
            LEFT JOIN REPRESENTANTES ON NOTA_FISCAL02.REPRCODIGO = REPRESENTANTES.REPRCODIGO
            WHERE (NOTA_FISCAL02.NF02MARCAFIM IS NULL OR NOTA_FISCAL02.NF02MARCAFIM = "Não")
              AND NOTA_FISCAL01.NF01VENDAORCA <> "Condicional Fechado"
              AND NOTA_FISCAL01.NF01DATA BETWEEN %s AND %s
            GROUP BY NOTA_FISCAL01.NF01SEQUENCIA, NOTA_FISCAL02.NF02SEQUENCIA
            ORDER BY NOTA_FISCAL01.NF01DATA, NOTA_FISCAL01.NF01SEQUENCIA, NOTA_FISCAL02.NF02SEQUENCIA;
            """
            df = pd.read_sql(query, connection, params=[data_inicio, data_fim])
            connection.close()
            return df
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return pd.DataFrame()

# Função para atualizar o CSV com novos dados
def atualizar_csv(data_inicio, data_fim):
    df_existente = carregar_csv()
    novos_dados = consultar_dados_periodo(data_inicio, data_fim)

    if not novos_dados.empty:
        df_atualizado = pd.concat([df_existente, novos_dados]).drop_duplicates().reset_index(drop=True)
        csv_path = Path(__file__).parent / 'dados_vendas.csv'
        df_atualizado.to_csv(csv_path, index=False)
        st.success("CSV atualizado com novos dados.")
    else:
        st.warning("Nenhum novo dado para atualizar.")

# Interface do usuário para seleção do período e atualização do CSV
st.title("Atualizar Dados de Vendas")

data_inicio = st.date_input("Selecione a data de início:", value=pd.to_datetime("2023-01-01"))
data_fim = st.date_input("Selecione a data de fim:", value=pd.to_datetime("today"))

if st.button("Atualizar CSV"):
    if data_inicio > data_fim:
        st.error("A data de início deve ser anterior ou igual à data de fim.")
    else:
        atualizar_csv(data_inicio, data_fim)
