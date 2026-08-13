import streamlit as st
import pandas as pd
import plotly.express as px
from database import buscar_vendas_reais, buscar_estoque_real

# Configuração da Página
st.set_page_config(
    page_title="Dashboard de Vendas & Estoque - Rede Market",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Leve
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# FUNÇÃO DE AUTENTICAÇÃO (SISTEMA DE LOGIN SEGURO)
# -------------------------------------------------------------
def check_password():
    """Retorna True se o usuário digitou a senha correta configurada nos Secrets."""
    def password_entered():
        # Compara a senha digitada com a chave PASSWORD nos Secrets do Streamlit
        if st.session_state["password"] == st.secrets.get("PASSWORD", ""):
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Não mantém a senha na memória
        else:
            st.session_state["authenticated"] = False

    # Se já estiver autenticado na sessão, libera o acesso
    if st.session_state.get("authenticated", False):
        return True

    # Tela de Login
    st.title("🔒 Acesso Restrito - Rede Market")
    st.text_input("Digite a senha do sistema:", type="password", on_change=password_entered, key="password")
    
    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("😕 Senha incorreta. Tente novamente.")
        
    return False

# -------------------------------------------------------------
# EXECUÇÃO DO APLICATIVO
# -------------------------------------------------------------
if check_password():
    
    # -------------------------------------------------------------
    # CARREGAMENTO DE DADOS COM CACHE (API / FIREBIRD)
    # -------------------------------------------------------------
    @st.cache_data(ttl=300) # Atualiza a cada 5 min ou quando clica no botão
    def load_sales():
        return buscar_vendas_reais(data_inicio='2026-01-01')

    @st.cache_data(ttl=300)
    def load_inventory():
        return buscar_estoque_real()

    # Carregamento dos dados reais
    try:
        df_sales = load_sales()
        df_inv = load_inventory()
    except Exception as e:
        st.error(f"Erro ao conectar com a API do Banco de Dados: {e}")
        st.stop()

    # -------------------------------------------------------------
    # MENU LATERAL & NAVEGAÇÃO
    # -------------------------------------------------------------
    st.sidebar.title("Navegação & Operações")
    
    # 🔄 Botão de Atualizar Dados em Tempo Real
    if st.sidebar.button("🔄 Atualizar Dados do Banco", use_container_width=True):
        st.cache_data.clear()  # Limpa o cache para forçar a nova consulta à API
        st.sidebar.success("Dados atualizados com sucesso!")
        st.rerun()

    st.sidebar.divider()

    page = st.sidebar.radio("Selecione a Visão:", [
        "📊 Vendas & Faturamento",
        "📦 Estoque Lojas vs. Indústria (IN)",
        "⚠️ Alertas de Reposição Crítica"
    ])

    st.sidebar.divider()

    # -------------------------------------------------------------
    # PÁGINA 1: VENDAS & FATURAMENTO
    # -------------------------------------------------------------
    if page == "📊 Vendas & Faturamento":
        st.title("📊 Painel Executivo de Vendas")
        
        if df_sales.empty:
            st.warning("Nenhum dado de vendas encontrado para o período selecionado.")
        else:
            # Filtro de Loja
            lojas_disponiveis = sorted(df_sales["LOJA"].astype(str).unique())
            lojas_selecionadas = st.multiselect(
                "Filtrar Lojas para Análise:",
                options=lojas_disponiveis,
                default=lojas_disponiveis
            )

            # Filtrando o DataFrame
            df_filtered = df_sales[df_sales["LOJA"].astype(str).isin(lojas_selecionadas)]

            # KPIs Calculados
            total_fat = df_filtered["VALOR_TOTAL_VENDIDO"].sum()
            total_qtd = df_filtered["QTD_VENDIDA_TOTAL"].sum()
            punit_medio = total_fat / total_qtd if total_qtd > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Faturamento Total", f"R$ {total_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("Volume Total Vendido", f"{total_qtd:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("Preço Médio / kg", f"R$ {punit_medio:.2f}".replace(".", ","))

            st.divider()
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🏆 Top Produtos por Loja (Volume em kg)")
                
                fig_vol = px.bar(
                    df_filtered.sort_values(by="QTD_VENDIDA_TOTAL", ascending=True),
                    x="QTD_VENDIDA_TOTAL", 
                    y="PRODUTO", 
                    color="LOJA",
                    barmode="group",
                    orientation='h',
                    labels={"QTD_VENDIDA_TOTAL": "Volume (kg)", "PRODUTO": "", "LOJA": "Loja"},
                    template="plotly_dark"
                )
                fig_vol.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_vol, use_container_width=True)

            with c2:
                st.subheader("💰 Faturamento por Loja")
                
                df_pie = df_filtered.groupby("LOJA")["VALOR_TOTAL_VENDIDO"].sum().reset_index()
                fig_fat = px.pie(
                    df_pie,
                    names="LOJA", 
                    values="VALOR_TOTAL_VENDIDO", 
                    hole=0.4,
                    labels={"LOJA": "Loja", "VALOR_TOTAL_VENDIDO": "Faturamento R$"},
                    template="plotly_dark"
                )
                fig_fat.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_fat, use_container_width=True)

            st.divider()
            
            # Visão em Abas para Detalhamento Individual por Loja
            st.subheader("🔍 Detalhamento por Filial")
            tabs = st.tabs([f"🏪 Loja {loja}" for loja in lojas_disponiveis])

            for i, loja in enumerate(lojas_disponiveis):
                with tabs[i]:
                    df_loja = df_sales[df_sales["LOJA"].astype(str) == loja].sort_values(by="QTD_VENDIDA_TOTAL", ascending=False)
                    
                    fat_loja = df_loja["VALOR_TOTAL_VENDIDO"].sum()
                    qtd_loja = df_loja["QTD_VENDIDA_TOTAL"].sum()
                    
                    m1, m2 = st.columns(2)
                    m1.metric(f"Faturamento Loja {loja}", f"R$ {fat_loja:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    m2.metric(f"Volume Loja {loja}", f"{qtd_loja:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
                    
                    st.dataframe(
                        df_loja[["PRODUTO", "QTD_VENDIDA_TOTAL", "VALOR_TOTAL_VENDIDO"]],
                        use_container_width=True,
                        column_config={
                            "PRODUTO": "Produto",
                            "QTD_VENDIDA_TOTAL": st.column_config.NumberColumn("Qtd Vendida (kg)", format="%.2f kg"),
                            "VALOR_TOTAL_VENDIDO": st.column_config.NumberColumn("Faturamento", format="R$ %.2f")
                        }
                    )

   # -------------------------------------------------------------
    # PÁGINA 2: ESTOQUE LOJAS VS INDÚSTRIA
    # -------------------------------------------------------------
    elif page == "📦 Estoque Lojas vs. Indústria (IN)":
        st.title("📦 Consulta e Comparativo de Estoque")
        st.caption("Visão geral dos saldos físicos na Indústria (IN) e nas Filiais")

        if df_inv.empty:
            st.warning("Sem dados de estoque disponíveis no momento.")
        else:
            # 1. BARRA DE FILTRO E PESQUISA
            col_busca, col_filtro = st.columns([2, 1])
            
            with col_busca:
                termo_busca = st.text_input("🔍 Buscar Produto por Nome ou Código:", "")
            
            # Aplica o filtro de busca se houver digitação
            df_exibicao = df_inv.copy()
            if termo_busca:
                termo = termo_busca.lower()
                df_exibicao = df_exibicao[
                    df_exibicao["PRODUTO"].astype(str).str.lower().str.contains(termo) |
                    df_exibicao["IDPRODUTO"].astype(str).str.contains(termo)
                ]

            # 2. DEFINIÇÃO DAS COLUNAS LIMPAS (Sem Mínimo Recomendado)
            colunas_estoque = [
                "IDPRODUTO", 
                "PRODUTO", 
                "Indústria (IN)", 
                "Maricá", 
                "Barra", 
                "Inoã", 
                "Ceasa Irajá"
            ]
            
            # Filtra apenas colunas que existem no DataFrame
            cols_finais = [c for c in colunas_estoque if c in df_exibicao.columns]

            # 3. EXIBIÇÃO DA TABELA
            st.dataframe(
                df_exibicao[cols_finais],
                use_container_width=True,
                hide_index=True
            )

            # 4. CARD DETALHADO CASO ENCONTRE UM ÚNICO PRODUTO OU SEJA SELECIONADO
            st.markdown("---")
            st.subheader("🔍 Detalhamento por Item")
            
            lista_produtos = df_inv["PRODUTO"].unique().tolist()
            produto_sel = st.selectbox("Selecione um Produto para ver os detalhes completos:", ["Todos"] + lista_produtos)

            if produto_sel != "Todos":
                item_dados = df_inv[df_inv["PRODUTO"] == produto_sel].iloc[0]
                
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("🏭 Indústria (IN)", f"{item_dados.get('Indústria (IN)', 0):,.2f} kg")
                c2.metric("🏪 Maricá", f"{item_dados.get('Maricá', 0):,.2f} kg")
                c3.metric("🏪 Barra", f"{item_dados.get('Barra', 0):,.2f} kg")
                c4.metric("🏪 Inoã", f"{item_dados.get('Inoã', 0):,.2f} kg")
                c5.metric("🏪 Ceasa Irajá", f"{item_dados.get('Ceasa Irajá', 0):,.2f} kg")

   # -------------------------------------------------------------
    # PÁGINA 3: ALERTAS DE REPOSIÇÃO CRÍTICA
    # -------------------------------------------------------------
    elif page == "⚠️ Alertas de Reposição Crítica":
        st.title("⚠️ Central de Alertas e Reposição")
        st.caption("Produtos com estoque em loja abaixo da média semanal de vendas da própria filial")

        if df_inv.empty:
            st.warning("Sem dados de estoque para calcular alertas.")
        else:
            tab1, tab2, tab3, tab4 = st.tabs([
                "🔴 Maricá", 
                "🔴 Barra", 
                "🔴 Inoã", 
                "🔴 Ceasa Irajá"
            ])

            lojas = [
                (tab1, "Maricá"),
                (tab2, "Barra"),
                (tab3, "Inoã"),
                (tab4, "Ceasa Irajá")
            ]

            for tab, nome_loja in lojas:
                with tab:
                    col_minimo = f"MINIMO_{nome_loja}"
                    
                    if nome_loja in df_inv.columns and col_minimo in df_inv.columns:
                        # Considera crítico APENAS o produto que vende na loja (mínimo > 0) 
                        # e cujo estoque atual é menor que a média semanal daquela loja
                        criticos = df_inv[
                            (df_inv[col_minimo] > 0) & 
                            (df_inv[nome_loja] < df_inv[col_minimo])
                        ]
                        
                        st.warning(f"Existem **{len(criticos)}** produtos com reposição necessária em {nome_loja}.")
                        
                        for _, row in criticos.iterrows():
                            qtd_atual = row[nome_loja]
                            qtd_minima = row[col_minimo]
                            estoque_ind = row.get('Indústria (IN)', 0)
                            
                            with st.expander(f"⚠️ {row['PRODUTO']} (Atual: {qtd_atual} kg | Mín. Semanal {nome_loja}: {qtd_minima} kg)"):
                                st.write(f"**Estoque Disponível na Indústria (IN):** `{estoque_ind} kg`")
                                
                                necessidade = qtd_minima - qtd_atual
                                if estoque_ind >= necessidade:
                                    st.success(f"✅ Indústria possui saldo suficiente para abastecer ({necessidade:.2f} kg necessários)!")
                                else:
                                    st.error(f"❌ Atenção: Saldo na Indústria é insuficiente para a necessidade de {necessidade:.2f} kg!")
                    else:
                        st.info(f"Sem dados de estoque para a loja {nome_loja}.")

    # -------------------------------------------------------------
    # BOTÃO DE LOGOUT
    # -------------------------------------------------------------
    if st.sidebar.button("🔒 Sair / Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
