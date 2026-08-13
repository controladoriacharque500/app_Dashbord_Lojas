import streamlit as st
import pandas as pd
import requests

API_URL = st.secrets.get("API_URL", "")

NOMES_LOJAS = {
    "01": "Maricá", "1": "Maricá",
    "02": "Barra", "2": "Barra",
    "03": "Inoã", "3": "Inoã",
    "04": "Ceasa Irajá", "4": "Ceasa Irajá",
    "IN": "Indústria"
}

def buscar_vendas_reais(data_inicio='2026-01-01'):
    if not API_URL:
        st.error("URL da API não configurada!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/vendas?data_inicio={data_inicio}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty and "LOJA" in df.columns:
                df["LOJA"] = df["LOJA"].astype(str).str.strip().map(
                    lambda x: NOMES_LOJAS.get(x, f"Loja {x}")
                )
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar Vendas: {e}")
        return pd.DataFrame()


def buscar_estoque_real():
    if not API_URL:
        st.error("URL da API não configurada!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/estoque"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            
            if not df.empty:
                # 1. Busca o histórico de vendas para saber o que é Produto Comercial Final
                df_vendas = buscar_vendas_reais()
                
                if not df_vendas.empty:
                    # Lista apenas IDs de produtos que tiveram alguma venda comercial
                    produtos_vendaveis = df_vendas["IDPRODUTO"].unique()
                    
                    # FILTRO CRÍTICO: Mantém no estoque APENAS produtos que são vendidos
                    df = df[df["IDPRODUTO"].isin(produtos_vendaveis)].copy()
                    
                    # Calcula Mínimo Semanal com base nas vendas reais
                    media_vendas = df_vendas.groupby("IDPRODUTO")["QTD_VENDIDA_TOTAL"].sum() / 4.3
                    df["MINIMO_RECOMENDADO"] = df["IDPRODUTO"].map(media_vendas).fillna(10.0).round(2)
                else:
                    df["MINIMO_RECOMENDADO"] = 10.0
                
                # 2. Renomeia as colunas das lojas
                renomear_colunas = {
                    "ESTOQUE_LOJA_01": "Maricá",
                    "ESTOQUE_LOJA_02": "Barra",
                    "ESTOQUE_LOJA_03": "Inoã",
                    "ESTOQUE_LOJA_04": "Ceasa Irajá",
                    "ESTOQUE_IN": "Indústria (IN)"
                }
                df.rename(columns=renomear_colunas, inplace=True)
                
                # 3. Elimina itens onde TODAS as lojas e a Indústria estão com estoque zerado
                colunas_estoque = ["Indústria (IN)", "Maricá", "Barra", "Inoã", "Ceasa Irajá"]
                cols_validas = [c for c in colunas_estoque if c in df.columns]
                
                if cols_validas:
                    # Mantém apenas se tiver saldo em pelo menos um local
                    df = df[df[cols_validas].abs().sum(axis=1) > 0]

            return df
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar Estoque: {e}")
        return pd.DataFrame()
