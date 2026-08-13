import pandas as pd
import fdb

# Configurações do seu banco de dados Firebird
DB_CONFIG = {
    'dsn': 'localhost:C:/caminho/para/seu/fdcmarket.gdb',  # Altere para o IP/caminho do servidor
    'user': 'SYSDBA',
    'password': 'masterkey',  # Altere para sua senha
    'charset': 'WIN1252'     # Ajuste o charset se necessário
}

def get_connection():
    return fdb.connect(**DB_CONFIG)

def buscar_vendas_reais(data_inicio='2026-01-01'):
    query = f"""
        SELECT 
            s.IDFILIAL AS LOJA,
            i.IDPRODUTO,
            p.DESCRICAOPRODUTO AS PRODUTO,
            ROUND(SUM(i.QTDE), 2) AS QTD_VENDIDA_TOTAL,
            ROUND(SUM(i.QTDE * i.PUNIT), 2) AS VALOR_TOTAL_VENDIDO
        FROM SAIDA s
        INNER JOIN ITEMSAIDA i 
            ON i.NUMEROSAIDA = s.NUMEROSAIDA 
           AND i.IDFILIAL = s.IDFILIAL
        LEFT JOIN PRODUTO p 
            ON p.IDPRODUTO = i.IDPRODUTO
        WHERE s.DATASAIDA >= '{data_inicio}'
        GROUP BY 
            s.IDFILIAL, 
            i.IDPRODUTO, 
            p.DESCRICAOPRODUTO
        ORDER BY 
            LOJA, 
            QTD_VENDIDA_TOTAL DESC;
    """
    
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

def buscar_estoque_real():
    # Exemplo de consulta do estoque atual nas Lojas vs. Indústria (IN)
    query = """
        SELECT 
            e.IDPRODUTO,
            p.DESCRICAOPRODUTO AS PRODUTO,
            SUM(CASE WHEN e.IDFILIAL = 'IN' THEN e.ESTOQUEATUAL ELSE 0 END) AS ESTOQUE_IN,
            SUM(CASE WHEN e.IDFILIAL = '01' THEN e.ESTOQUEATUAL ELSE 0 END) AS ESTOQUE_LOJA_01,
            SUM(CASE WHEN e.IDFILIAL = '02' THEN e.ESTOQUEATUAL ELSE 0 END) AS ESTOQUE_LOJA_02,
            SUM(CASE WHEN e.IDFILIAL = '03' THEN e.ESTOQUEATUAL ELSE 0 END) AS ESTOQUE_LOJA_03,
            SUM(CASE WHEN e.IDFILIAL = '04' THEN e.ESTOQUEATUAL ELSE 0 END) AS ESTOQUE_LOJA_04,
            p.ESTOQUEMINIMO AS MINIMO_RECOMENDADO
        FROM ESTOQUE e
        INNER JOIN PRODUTO p ON p.IDPRODUTO = e.IDPRODUTO
        GROUP BY e.IDPRODUTO, p.DESCRICAOPRODUTO, p.ESTOQUEMINIMO;
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df
