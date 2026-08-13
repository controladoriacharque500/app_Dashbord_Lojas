import streamlit as st
import pandas as pd
import plotly.express as px
from database import PALETA_CORES
from database import buscar_vendas_reais, buscar_estoque_real

# -------------------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO NO PADRÃO BRASILEIRO (PT-BR)
# -------------------------------------------------------------
def formatar_br(valor, sufixo="", prefixo=""):
    """
    Formata um número float para o padrão brasileiro: 183.180.959,97
    """
    if valor is None or pd.isna(valor):
        return f"{prefixo}0,00{sufixo}"
    
    # Formata em padrão americano primeiro (com vírgula nos milhares)
    texto = f"{valor:,.2f}"
    # Inverte ponto por vírgula e vírgula por ponto
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"{prefixo}{texto}{sufixo}"

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

        df_vendas = buscar_vendas_reais()

        if df_vendas.empty:
            st.warning("Sem dados de vendas disponíveis no momento.")
        else:
            # --- FILTROS EXECUTIVOS (LOJAS E DATAS) ---
            st.markdown("### 🔍 Filtros de Análise")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                lojas_disponiveis = df_vendas["LOJA"].unique().tolist()
                lojas_sel = st.multiselect("Filtrar Lojas:", lojas_disponiveis, default=lojas_disponiveis)

            # Filtro por Período/Data
            df_filtrado = df_vendas[df_vendas["LOJA"].isin(lojas_sel)].copy()

            if "DATA" in df_filtrado.columns and not df_filtrado["DATA"].isnull().all():
                min_date = df_filtrado["DATA"].min().date()
                max_date = df_filtrado["DATA"].max().date()

                with col2:
                    periodo_sel = st.date_input(
                        "Período das Vendas:",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                
                # Aplica o intervalo de datas selecionado
                if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
                    dt_inicio, dt_fim = periodo_sel
                    df_filtrado = df_filtrado[
                        (df_filtrado["DATA"].dt.date >= dt_inicio) & 
                        (df_filtrado["DATA"].dt.date <= dt_fim)
                    ]

            # --- CARDS DE RESUMO (KPIs FORMATADOS EM PT-BR) ---
            st.markdown("---")
            kpi1, kpi2, kpi3 = st.columns(3)
            
            fat_total = df_filtrado["FATURAMENTO_TOTAL"].sum()
            vol_total = df_filtrado["QTD_VENDIDA_TOTAL"].sum()
            preco_medio = fat_total / vol_total if vol_total > 0 else 0

            # Aplica a formatação PT-BR
            kpi1.metric("Faturamento Total", formatar_br(fat_total, prefixo="R$ "))
            kpi2.metric("Volume Total Vendido", formatar_br(vol_total, sufixo=" kg"))
            kpi3.metric("Preço Médio / kg", formatar_br(preco_medio, prefixo="R$ "))

            # --- GRÁFICOS COM CORES PADRONIZADAS ---
            st.markdown("---")
            g1, g2 = st.columns(2)

            with g1:
                st.subheader("🏆 Volume por Loja (kg)")
                
                # 1. Filtra subprodutos industriais / graxaria que não devem entrar na análise executiva
                df_grafico = df_filtrado[
                    ~df_filtrado["PRODUTO"].astype(str).str.upper().str.contains("RESIDUO NAO COMESTIVEL|GRAXARIA|SOBRAS", na=False)
                ].copy()

                # 2. Descobre os TOP 10 produtos ÚNICOS em volume total (soma de todas as lojas)
                top_10_produtos = (
                    df_grafico.groupby("PRODUTO")["QTD_VENDIDA_TOTAL"]
                    .sum()
                    .nlargest(10)
                    .index
                )

                # 3. Filtra apenas os dados desses 10 produtos e agrupa por produto e loja
                df_top10 = df_grafico[df_grafico["PRODUTO"].isin(top_10_produtos)]
                df_top_agrupado = df_top10.groupby(["PRODUTO", "LOJA"])["QTD_VENDIDA_TOTAL"].sum().reset_index()

                # 4. Renderiza o gráfico com os 10 produtos reais
                fig_bar = px.bar(
                    df_top_agrupado,
                    x="QTD_VENDIDA_TOTAL",
                    y="PRODUTO",
                    color="LOJA",
                    orientation="h",
                    color_discrete_map=PALETA_CORES,  # 🎨 Mantém a paleta por loja
                    title="Top 10 Produtos Mais Vendidos"
                )
                fig_bar.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    xaxis_title="Quantidade Vendida (kg)",
                    yaxis_title=""
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with g2:
                st.subheader("💰 Faturamento por Loja")
                df_pie = df_filtrado.groupby("LOJA")["FATURAMENTO_TOTAL"].sum().reset_index()

                fig_pie = px.pie(
                    df_pie,
                    values="FATURAMENTO_TOTAL",
                    names="LOJA",
                    color="LOJA",
                    color_discrete_map=PALETA_CORES,  # 🎨 Aplica a paleta fixa!
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.divider()
            
            # Visão em Abas para Detalhamento Individual por Loja
            st.subheader("🔍 Detalhamento por Filial")
            tabs = st.tabs([f"🏪 Loja {loja}" for loja in lojas_disponiveis])

            for i, loja in enumerate(lojas_disponiveis):
                with tabs[i]:
                    df_loja = df_sales[df_sales["LOJA"].astype(str) == loja].sort_values(by="QTD_VENDIDA_TOTAL", ascending=False)
                    
                    fat_loja = df_loja["VALOR_TOTAL_VENDIDO"].sum() if "VALOR_TOTAL_VENDIDO" in df_loja.columns else df_loja["FATURAMENTO_TOTAL"].sum()
                    qtd_loja = df_loja["QTD_VENDIDA_TOTAL"].sum()
                    
                    m1, m2 = st.columns(2)
                    m1.metric(f"Faturamento Loja {loja}", formatar_br(fat_loja, prefixo="R$ "))
                    m2.metric(f"Volume Loja {loja}", formatar_br(qtd_loja, sufixo=" kg"))
                    
                    col_valor = "VALOR_TOTAL_VENDIDO" if "VALOR_TOTAL_VENDIDO" in df_loja.columns else "FATURAMENTO_TOTAL"
                    
                    st.dataframe(
                        df_loja[["PRODUTO", "QTD_VENDIDA_TOTAL", col_valor]],
                        use_container_width=True,
                        column_config={
                            "PRODUTO": "Produto",
                            "QTD_VENDIDA_TOTAL": st.column_config.NumberColumn("Qtd Vendida (kg)", format="%.2f kg"),
                            col_valor: st.column_config.NumberColumn("Faturamento", format="R$ %.2f")
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
                c1.metric("🏭 Indústria (IN)", formatar_br(item_dados.get('Indústria (IN)', 0), sufixo=" kg"))
                c2.metric("🏪 Maricá", formatar_br(item_dados.get('Maricá', 0), sufixo=" kg"))
                c3.metric("🏪 Barra", formatar_br(item_dados.get('Barra', 0), sufixo=" kg"))
                c4.metric("🏪 Inoã", formatar_br(item_dados.get('Inoã', 0), sufixo=" kg"))
                c5.metric("🏪 Ceasa Irajá", formatar_br(item_dados.get('Ceasa Irajá', 0), sufixo=" kg"))

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
                            
                            with st.expander(f"⚠️ {row['PRODUTO']} (Atual: {formatar_br(qtd_atual, sufixo=' kg')} | Mín. Semanal {nome_loja}: {formatar_br(qtd_minima, sufixo=' kg')})"):
                                st.write(f"**Estoque Disponível na Indústria (IN):** `{formatar_br(estoque_ind, sufixo=' kg')}`")
                                
                                necessidade = qtd_minima - qtd_atual
                                if estoque_ind >= necessidade:
                                    st.success(f"✅ Indústria possui saldo suficiente para abastecer ({formatar_br(necessidade, sufixo=' kg')} necessários)!")
                                else:
                                    st.error(f"❌ Atenção: Saldo na Indústria é insuficiente para a necessidade de {formatar_br(necessidade, sufixo=' kg')}!")
                    else:
                        st.info(f"Sem dados de estoque para a loja {nome_loja}.")

    # -------------------------------------------------------------
    # BOTÃO DE LOGOUT
    # -------------------------------------------------------------
    if st.sidebar.button("🔒 Sair / Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
