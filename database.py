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
        # O cabeçalho 'ngrok-skip-browser-warning' evita que o Ngrok interrompa
        # a requisição automática com uma página HTML de aviso.
        headers = {"ngrok-skip-browser-warning": "69420"}
        
        url = f"{API_URL}/vendas?data_inicio={data_inicio}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            return df
        else:
            st.error(f"Erro de resposta da API Local: Código HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Não foi possível conectar à API Local. Verifique se a API e o Ngrok estão ativos. Detalhe: {e}")
        return pd.DataFrame()
