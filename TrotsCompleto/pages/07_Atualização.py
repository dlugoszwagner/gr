import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Função para conectar ao banco de dados MySQL
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            # host='Servidor',
            host='trots.nsupdate.info',
            database='comercio',
            user='Trots2303',
            password='Trots2303#2024',
            # port=3306,
            port=3324,
            charset='utf8'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Função para executar a query e obter os dados
def get_data(connection, start_date, end_date):
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
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(result)

# Configuração da interface Streamlit
st.title('Consulta de Vendas')

# Seleção do período
start_date = st.date_input('Data Inicial')
end_date = st.date_input('Data Final')

if st.button('Consultar'):
    connection = connect_to_db()
    if connection:
        data = get_data(connection, start_date, end_date)
        connection.close()
        
        if not data.empty:
            st.write(data)
            # Cria o arquivo CSV
            data.to_csv('venda.csv', index=False)
            st.success('Arquivo venda.csv criado com sucesso!')
            st.download_button(label="Download CSV", data=data.to_csv(index=False), file_name='venda.csv', mime='text/csv')
        else:
            st.warning('Nenhum dado encontrado para o período selecionado.')
