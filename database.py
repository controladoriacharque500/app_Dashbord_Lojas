import streamlit as st
import pandas as pd
import requests

# Busca a URL definida nos Secrets do Streamlit
API_URL = st.secrets.get("API_URL", "")

def buscar_vendas_reais(data_inicio='2026-01-01'):
    """
    Busca os dados de vendas chamando a API local exposta pelo Ngrok.
    """
    if not API_URL:
        st.error("URL da API não configurada nos Secrets (API_URL)!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/vendas?data_inicio={data_inicio}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            return pd.DataFrame(dados)
        else:
            st.error(f"Erro de resposta da API (Vendas): Código HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Não foi possível conectar à API de Vendas: {e}")
        return pd.DataFrame()


def buscar_estoque_real():
    """
    Busca os dados de estoque chamando a API local exposta pelo Ngrok.
    """
    if not API_URL:
        st.error("URL da API não configurada nos Secrets (API_URL)!")
        return pd.DataFrame()

    try:
        headers = {"ngrok-skip-browser-warning": "69420"}
        url = f"{API_URL}/estoque"  # Rota da API para estoque
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            return pd.DataFrame(dados)
        else:
            st.error(f"Erro de resposta da API (Estoque): Código HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Não foi possível conectar à API de Estoque: {e}")
        return pd.DataFrame()
