import pandas as pd
import requests

# URL pública gerada pelo seu Ngrok
API_URL = "https://surpass-entwine-sasquatch.ngrok-free.dev"

def buscar_vendas_reais(data_inicio='2026-01-01'):
    try:
        # Cabeçalho para o Ngrok liberar a requisição gratuita sem tela de aviso
        headers = {"ngrok-skip-browser-warning": "69420"}
        
        url = f"{API_URL}/vendas?data_inicio={data_inicio}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            return df
        else:
            print(f"Erro na API: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Erro ao conectar com a API local: {e}")
        return pd.DataFrame()
