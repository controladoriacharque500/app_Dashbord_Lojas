import streamlit as st
import pandas as pd
import plotly.express as px

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
# 1. AUTENTICAÇÃO E LOGIN
# -------------------------------------------------------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Login - Gestão de Estoque & Vendas")
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            if submit:
                # Altere os usuários/senhas conforme necessário
                if username in ["gerente", "admin", "loja01", "loja03"] and password == "123456":
                    st.session_state["authenticated"] = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        return False
    return True

if check_password():
    # -------------------------------------------------------------
    # 2. MENU E FILTROS
    # -------------------------------------------------------------
    st.sidebar.title("Navegação & Filtros")

    page = st.sidebar.radio("Selecione a Visão:", [
        "📊 Vendas & Faturamento",
        "📦 Estoque Lojas vs. Indústria (IN)",
        "⚠️ Alertas de Reposição Crítica"
    ])

    # Simulador de Dados (Substitua depois pelo retorno direto da query no Firebird)
    @st.cache_data
    def load_sales_data():
        data = {
            "LOJA": ["01", "01", "01", "01", "03", "03", "03", "03"],
            "IDPRODUTO": ["1.513", "1.607", "1.505", "1.499", "1.513", "1.607", "1.505", "1.499"],
            "PRODUTO": [
                "ACEM BOVINO RESF", "ALCATRA COM MAMINHA BOVINO RESF",
                "PATINHO BOVINO RESF", "CONTRA FILE BOVINO RESF",
                "ACEM BOVINO RESF", "ALCATRA COM MAMINHA BOVINO RESF",
                "PATINHO BOVINO RESF", "CONTRA FILE BOVINO RESF"
            ],
            "QTD_VENDIDA_TOTAL": [16461.28, 15095.41, 11625.60, 10325.99, 12400.50, 11200.00, 8900.20, 7800.10],
            "VALOR_TOTAL_VENDIDO": [546798.32, 662975.20, 416838.23, 489157.16, 412000.00, 492000.00, 319000.00, 369000.00]
        }
        return pd.DataFrame(data)

    @st.cache_data
    def load_inventory_data():
        data = {
            "IDPRODUTO": ["1.513", "1.607", "1.505", "1.499", "2.404", "1.519", "3.976", "1.501"],
            "PRODUTO": [
                "ACEM BOVINO RESF", "ALCATRA COM MAMINHA BOVINO RESF",
                "PATINHO BOVINO RESF", "CONTRA FILE BOVINO RESF",
                "FILE DE COSTELA BOV RESF", "PEITO BOVINO RESF",
                "TOUCINHO CONGELADO DE SUINO", "COXAO MOLE BOVINO RESF"
            ],
            "ESTOQUE_IN": [15000.0, 8000.0, 12000.0, 4500.0, 9000.0, 3000.0, 11000.0, 6500.0],
            "ESTOQUE_LOJA_01": [450.0, 120.0, 850.0, 90.0, 300.0, 50.0, 1200.0, 210.0],
            "ESTOQUE_LOJA_03": [600.0, 350.0, 200.0, 150.0, 180.0, 400.0, 800.0, 95.0],
            "MINIMO_RECOMENDADO": [500.0, 300.0, 400.0, 250.0, 200.0, 150.0, 500.0, 300.0]
        }
        return pd.DataFrame(data)

    df_sales = load_sales_data()
    df_inv = load_inventory_data()

   # -------------------------------------------------------------
    # PÁGINA 1: VENDAS & FATURAMENTO
    # -------------------------------------------------------------
    if page == "📊 Vendas & Faturamento":
        st.title("📊 Painel Executivo de Vendas")
        
        # Filtro de Loja no topo do painel
        lojas_disponiveis = sorted(df_sales["LOJA"].unique())
        lojas_selecionadas = st.multiselect(
            "Filtrar Lojas para Análise:",
            options=lojas_disponiveis,
            default=lojas_disponiveis
        )

        # Filtrando o dataframe com base na seleção
        df_filtered = df_sales[df_sales["LOJA"].isin(lojas_selecionadas)]

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
            
            # Gráfico Agrupado por Loja
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
            
            fig_fat = px.pie(
                df_filtered.groupby("LOJA")["VALOR_TOTAL_VENDIDO"].sum().reset_index(),
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
                df_loja = df_sales[df_sales["LOJA"] == loja].sort_values(by="QTD_VENDIDA_TOTAL", ascending=False)
                
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

        st.dataframe(
            df_inv,
            use_container_width=True,
            column_config={
                "IDPRODUTO": "Cód.",
                "PRODUTO": "Descrição do Produto",
                "ESTOQUE_IN": st.column_config.NumberColumn("Indústria (IN) [kg]", format="%.2f kg"),
                "ESTOQUE_LOJA_01": st.column_config.NumberColumn("Loja 01 [kg]", format="%.2f kg"),
                "ESTOQUE_LOJA_03": st.column_config.NumberColumn("Loja 03 [kg]", format="%.2f kg"),
                "MINIMO_RECOMENDADO": st.column_config.NumberColumn("Mínimo Recomendado", format="%.2f kg"),
            }
        )

        st.divider()
        st.subheader("🔍 Análise de Disponibilidade para Transferência")
        prod_select = st.selectbox("Selecione um Produto para Detalhamento:", df_inv["PRODUTO"].unique())
        prod_data = df_inv[df_inv["PRODUTO"] == prod_select].iloc[0]

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Estoque na Indústria (IN)", f"{prod_data['ESTOQUE_IN']:,.2f} kg")
        col_b.metric("Estoque Loja 01", f"{prod_data['ESTOQUE_LOJA_01']:,.2f} kg", delta=f"{prod_data['ESTOQUE_LOJA_01'] - prod_data['MINIMO_RECOMENDADO']:,.2f} kg")
        col_c.metric("Estoque Loja 03", f"{prod_data['ESTOQUE_LOJA_03']:,.2f} kg", delta=f"{prod_data['ESTOQUE_LOJA_03'] - prod_data['MINIMO_RECOMENDADO']:,.2f} kg")

    # -------------------------------------------------------------
    # PÁGINA 3: ALERTAS DE REPOSIÇÃO CRÍTICA
    # -------------------------------------------------------------
    elif page == "⚠️ Alertas de Reposição Crítica":
        st.title("⚠️ Central de Alertas e Reposição")
        st.caption("Produtos com estoque em loja abaixo do nível mínimo de segurança")

        criticos_01 = df_inv[df_inv["ESTOQUE_LOJA_01"] < df_inv["MINIMO_RECOMENDADO"]]
        criticos_03 = df_inv[df_inv["ESTOQUE_LOJA_03"] < df_inv["MINIMO_RECOMENDADO"]]

        tab1, tab2 = st.tabs(["🔴 Alertas Loja 01", "🔴 Alertas Loja 03"])

        with tab1:
            st.warning(f"Existem **{len(criticos_01)}** produtos abaixo do nível de segurança na Loja 01.")
            for _, row in criticos_01.iterrows():
                with st.expander(f"⚠️ {row['PRODUTO']} (Atual: {row['ESTOQUE_LOJA_01']} kg | Mínimo: {row['MINIMO_RECOMENDADO']} kg)"):
                    st.write(f"**Disponível na Indústria (IN) para transferência:** `{row['ESTOQUE_IN']} kg`")
                    if row['ESTOQUE_IN'] >= (row['MINIMO_RECOMENDADO'] - row['ESTOQUE_LOJA_01']):
                        st.success("✅ Indústria possui saldo suficiente para atender a reposição imediata!")
                    else:
                        st.error("❌ Atenção: Estoque na Indústria também está baixo!")

        with tab2:
            st.warning(f"Existem **{len(criticos_03)}** produtos abaixo do nível de segurança na Loja 03.")
            for _, row in criticos_03.iterrows():
                with st.expander(f"⚠️ {row['PRODUTO']} (Atual: {row['ESTOQUE_LOJA_03']} kg | Mínimo: {row['MINIMO_RECOMENDADO']} kg)"):
                    st.write(f"**Disponível na Indústria (IN) para transferência:** `{row['ESTOQUE_IN']} kg`")
                    if row['ESTOQUE_IN'] >= (row['MINIMO_RECOMENDADO'] - row['ESTOQUE_LOJA_03']):
                        st.success("✅ Indústria possui saldo suficiente para atender a reposição imediata!")
                    else:
                        st.error("❌ Atenção: Estoque na Indústria também está baixo!")

    # Botão de Logout
    st.sidebar.divider()
    if st.sidebar.button("🔒 Sair / Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
