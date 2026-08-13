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
                # Renomeia colunas para os nomes oficiais das lojas
                renomear_colunas = {
                    "ESTOQUE_LOJA_01": "Maricá",
                    "ESTOQUE_LOJA_02": "Barra",
                    "ESTOQUE_LOJA_03": "Inoã",
                    "ESTOQUE_LOJA_04": "Ceasa Irajá",
                    "ESTOQUE_IN": "Indústria (IN)"
                }
                df.rename(columns=renomear_colunas, inplace=True)
                
                # Cálculo do Mínimo Inteligente: Média semanal de vendas
                # Exemplo: Venda total acumulada dividida por ~4.3 semanas (1 mês)
                df_vendas = buscar_vendas_reais()
                if not df_vendas.empty:
                    media_vendas = df_vendas.groupby("IDPRODUTO")["QTD_VENDIDA_TOTAL"].sum() / 4.3
                    df["MINIMO_RECOMENDADO"] = df["IDPRODUTO"].map(media_vendas).fillna(50.0).round(2)
                else:
                    df["MINIMO_RECOMENDADO"] = 50.0 # Valor padrão caso não haja histórico de vendas
                    
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar Estoque: {e}")
        return pd.DataFrame()
