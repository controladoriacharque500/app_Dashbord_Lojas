import streamlit as st
import pandas as pd
import requests

API_URL = st.secrets.get("API_URL", "")

# Dicionário para renomear os códigos das filiais
NOMES_LOJAS = {
    "01": "Lj Maricá",
    "1": "Lj Maricá",
    "02": "Lj Barra",
    "2": "Lj Barra",
    "03": "Lj Inoã",
    "3": "Lj Inoã",
    "04": "Lj Ceasa Irajá",
    "4": "Lj Ceasa Irajá",
    "IN": "Indústria"
}

def buscar_vendas_reais(data_inicio='2026-01-01'):
    if not API_URL:
        st.error("URL da API não configurada nos Secrets (API_URL)!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/vendas?data_inicio={data_inicio}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            
            # Substitui os códigos/siglas pelos nomes amigáveis das lojas
            if not df.empty and "LOJA" in df.columns:
                df["LOJA"] = df["LOJA"].astype(str).str.strip().map(
                    lambda x: NOMES_LOJAS.get(x, f"Loja {x}")
                )
            return df
        else:
            st.error(f"Erro de resposta da API (Vendas): Código HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Não foi possível conectar à API de Vendas: {e}")
        return pd.DataFrame()


def buscar_estoque_real():
    if not API_URL:
        st.error("URL da API não configurada nos Secrets (API_URL)!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/estoque"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            return pd.DataFrame(dados)
        else:
            st.error(f"Erro de resposta da API (Estoque): Código HTTP {response.status_code} - Rota não encontrada no Servidor API local.")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Não foi possível conectar à API de Estoque: {e}")
        return pd.DataFrame()
