import streamlit as st
import pandas as pd
import requests

API_URL = st.secrets.get("API_URL", "")

# 🎨 PALETA DE CORES FIXA POR LOJA
PALETA_CORES = {
    "Indústria": "#1f77b4",     # Azul
    "Maricá": "#ff7f0e",        # Laranja
    "Barra": "#2ca02c",         # Verde
    "Inoã": "#9467bd",          # Roxo
    "Ceasa Irajá": "#d62728"    # Vermelho
}

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
            if not df.empty:
                if "LOJA" in df.columns:
                    df["LOJA"] = df["LOJA"].astype(str).str.strip().map(
                        lambda x: NOMES_LOJAS.get(x, f"Loja {x}")
                    )
                # Converte para datetime para permitir filtros avançados
                if "DATA" in df.columns:
                    df["DATA"] = pd.to_datetime(df["DATA"])
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
                # 1. Busca histórico de vendas para saber o giro individual por LOJA
                df_vendas = buscar_vendas_reais()
                
                if not df_vendas.empty:
                    # Filtra apenas produtos vendáveis
                    produtos_vendaveis = df_vendas["IDPRODUTO"].unique()
                    df = df[df["IDPRODUTO"].isin(produtos_vendaveis)].copy()
                    
                    # Média de vendas semanais POR LOJA E POR PRODUTO
                    # (Dividido por 4.3 para estimar 1 semana a partir do histórico mensal)
                    vendas_por_loja = df_vendas.groupby(["IDPRODUTO", "LOJA"])["QTD_VENDIDA_TOTAL"].sum() / 4.3
                    
                    # Cria colunas de mínimo individual para cada loja
                    # Mapeia o mínimo específico da filial (ex: MINIMO_Maricá, MINIMO_Barra, etc.)
                    lojas_map = {
                        "ESTOQUE_LOJA_01": "Maricá",
                        "ESTOQUE_LOJA_02": "Barra",
                        "ESTOQUE_LOJA_03": "Inoã",
                        "ESTOQUE_LOJA_04": "Ceasa Irajá"
                    }
                    
                    for col_estoque, nome_loja in lojas_map.items():
                        col_minimo = f"MINIMO_{nome_loja}"
                        # Busca a média de vendas específica desta loja para este produto
                        df[col_minimo] = df["IDPRODUTO"].apply(
                            lambda pid: vendas_por_loja.get((pid, nome_loja), 0.0)
                        ).round(2)
                
                # 2. Renomeia as colunas de estoque para os nomes amigáveis
                renomear_colunas = {
                    "ESTOQUE_LOJA_01": "Maricá",
                    "ESTOQUE_LOJA_02": "Barra",
                    "ESTOQUE_LOJA_03": "Inoã",
                    "ESTOQUE_LOJA_04": "Ceasa Irajá",
                    "ESTOQUE_IN": "Indústria (IN)"
                }
                df.rename(columns=renomear_colunas, inplace=True)
                
                # 3. Remove produtos com estoque totalmente zerado em todas as pontas
                colunas_estoque = ["Indústria (IN)", "Maricá", "Barra", "Inoã", "Ceasa Irajá"]
                cols_validas = [c for c in colunas_estoque if c in df.columns]
                if cols_validas:
                    df = df[df[cols_validas].abs().sum(axis=1) > 0]

            return df
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar Estoque: {e}")
        return pd.DataFrame()
