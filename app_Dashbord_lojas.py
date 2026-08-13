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
        st.title("📦 Comparativo de Estoque: Lojas vs. Indústria (IN)")
        st.caption("Verifique o saldo no Centro de Distribuição / Indústria (Filial IN) para abastecimento das lojas.")

        if df_inv.empty:
            st.warning("Sem dados de estoque disponíveis no momento.")
        else:
            colunas_exibicao = ["IDPRODUTO", "PRODUTO", "Indústria (IN)", "Maricá", "Barra", "Inoã", "Ceasa Irajá", "MINIMO_RECOMENDADO"]
            cols_presentes = [c for c in colunas_exibicao if c in df_inv.columns]
            
            st.dataframe(
                df_inv[cols_presentes],
                use_container_width=True,
                hide_index=True
            )

    # -------------------------------------------------------------
    # PÁGINA 3: ALERTAS DE REPOSIÇÃO CRÍTICA
    # -------------------------------------------------------------
    elif page == "⚠️ Alertas de Reposição Crítica":
        st.title("⚠️ Central de Alertas e Reposição")
        st.caption("Produtos com estoque em loja abaixo da média semanal de vendas (Nível de Segurança)")

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
                    if nome_loja in df_inv.columns:
                        criticos = df_inv[df_inv[nome_loja] < df_inv["MINIMO_RECOMENDADO"]]
                        st.warning(f"Existem **{len(criticos)}** produtos abaixo do nível de segurança em {nome_loja}.")
                        
                        for _, row in criticos.iterrows():
                            with st.expander(f"⚠️ {row['PRODUTO']} (Atual: {row[nome_loja]} kg | Mínimo Semanal: {row['MINIMO_RECOMENDADO']} kg)"):
                                st.write(f"**Estoque Disponível na Indústria:** `{row.get('Indústria (IN)', 0)} kg`")
                                if row.get('Indústria (IN)', 0) >= (row['MINIMO_RECOMENDADO'] - row[nome_loja]):
                                    st.success("✅ Indústria possui saldo suficiente para abastecimento!")
                                else:
                                    st.error("❌ Atenção: Estoque na Indústria também está crítico!")
                    else:
                        st.info(f"Sem dados de estoque para a loja {nome_loja}.")

    # -------------------------------------------------------------
    # BOTÃO DE LOGOUT
    # -------------------------------------------------------------
    if st.sidebar.button("🔒 Sair / Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
