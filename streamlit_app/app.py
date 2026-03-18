"""
Dashboard do Radar de Reputação - Reclame AQUI
Aplicação Streamlit para visualização de KPIs e análise de reclamações
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yaml
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Radar de Reputação - Reclame AQUI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Carrega configurações
@st.cache_data
def load_config():
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


# Carrega dados
@st.cache_data
def load_data():
    """Carrega dados processados para o dashboard"""
    data_dir = Path(__file__).parent.parent / "data" / "processed"

    complaints_file = data_dir / "reclamacoes_processadas.csv"
    kpis_file = data_dir / "kpis_empresas.csv"

    complaints_df = pd.DataFrame()
    kpis_df = pd.DataFrame()

    if complaints_file.exists():
        complaints_df = pd.read_csv(complaints_file, sep=";", encoding="utf-8-sig")
        complaints_df["data_reclamacao"] = pd.to_datetime(complaints_df["data_reclamacao"])

    if kpis_file.exists():
        kpis_df = pd.read_csv(kpis_file, sep=";", encoding="utf-8-sig")

    return complaints_df, kpis_df


complaints_df, kpis_df = load_data()

# Sidebar com filtros
st.sidebar.title("📊 Radar de Reputação")
st.sidebar.markdown("---")

# Filtros
if not complaints_df.empty:
    # Filtro de empresa
    empresas = sorted(complaints_df["empresa"].unique())
    empresa_selecionada = st.sidebar.multiselect(
        "🏢 Empresas", empresas, default=empresas[:3] if len(empresas) > 3 else empresas
    )

    # Filtro de período
    data_min = complaints_df["data_reclamacao"].min().date()
    data_max = complaints_df["data_reclamacao"].max().date()

    periodo = st.sidebar.date_input(
        "📅 Período",
        value=(data_max - timedelta(days=30), data_max),
        min_value=data_min,
        max_value=data_max,
    )

    # Filtro de status
    if "status" in complaints_df.columns:
        status_options = sorted(complaints_df["status"].unique())
        status_selecionado = st.sidebar.multiselect(
            "📋 Status", status_options, default=status_options
        )

    # Aplica filtros
    df_filtrado = complaints_df.copy()

    if empresa_selecionada:
        df_filtrado = df_filtrado[df_filtrado["empresa"].isin(empresa_selecionada)]

    if len(periodo) == 2:
        df_filtrado = df_filtrado[
            (df_filtrado["data_reclamacao"].dt.date >= periodo[0])
            & (df_filtrado["data_reclamacao"].dt.date <= periodo[1])
        ]

    if "status_selecionado" in locals() and status_selecionado:
        df_filtrado = df_filtrado[df_filtrado["status"].isin(status_selecionado)]

else:
    st.sidebar.warning("⚠️ Nenhum dado encontrado. Execute a coleta primeiro.")
    df_filtrado = pd.DataFrame()


# Função para criar métricas
def criar_metrica(titulo, valor, delta=None, delta_color="normal"):
    """Cria um componente de métrica padronizado"""
    if delta is not None:
        st.metric(titulo, valor, delta, delta_color)
    else:
        st.metric(titulo, valor)


# Header principal
st.title("📊 Radar de Reputação - Reclame AQUI")
st.markdown("Monitoramento e análise de reclamações em tempo real")

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado disponível com os filtros selecionados.")
    st.stop()

# KPIs principais
st.header("🎯 KPIs Principais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_reclamacoes = len(df_filtrado)
    criar_metrica("Total de Reclamações", f"{total_reclamacoes:,}")

with col2:
    reclamacoes_ultima_semana = len(
        df_filtrado[df_filtrado["data_reclamacao"] >= (datetime.now() - timedelta(days=7))]
    )
    criar_metrica("Última Semana", f"{reclamacoes_ultima_semana:,}")

with col3:
    if "avaliacao_consumidor" in df_filtrado.columns:
        media_avaliacao = df_filtrado["avaliacao_consumidor"].mean()
        criar_metrica("Avaliação Média", f"{media_avaliacao:.1f}⭐")
    else:
        criar_metrica("Avaliação Média", "N/A")

with col4:
    if "status" in df_filtrado.columns:
        resolvidas = len(
            df_filtrado[
                df_filtrado["status"].str.contains("Resolvida|Respondida", case=False, na=False)
            ]
        )
        taxa_resolucao = (resolvidas / total_reclamacoes * 100) if total_reclamacoes > 0 else 0
        criar_metrica("Taxa de Resolução", f"{taxa_resolucao:.1f}%")

st.markdown("---")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Reclamações por Empresa")

    if len(empresa_selecionada) > 1:
        reclamacoes_por_empresa = df_filtrado["empresa"].value_counts().reset_index()
        reclamacoes_por_empresa.columns = ["Empresa", "Reclamações"]

        fig = px.bar(
            reclamacoes_por_empresa,
            x="Empresa",
            y="Reclamações",
            title="Distribuição de Reclamações por Empresa",
            color="Reclamações",
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecione múltiplas empresas para ver a comparação")

with col2:
    st.subheader("📅 Tendência Temporal")

    reclamacoes_por_dia = (
        df_filtrado.groupby(df_filtrado["data_reclamacao"].dt.date)
        .size()
        .reset_index(name="Reclamações")
    )

    fig = px.line(
        reclamacoes_por_dia,
        x="data_reclamacao",
        y="Reclamações",
        title="Evolução das Reclamações",
        markers=True,
    )
    fig.update_xaxes(title="Data")
    fig.update_yaxes(title="Número de Reclamações")
    st.plotly_chart(fig, use_container_width=True)

# Status das reclamações
st.subheader("📋 Status das Reclamações")

if "status" in df_filtrado.columns:
    status_counts = df_filtrado["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Quantidade"]

    fig = px.pie(
        status_counts,
        values="Quantidade",
        names="Status",
        title="Distribuição por Status",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Dados de status não disponíveis")

# Tabela de reclamações recentes
st.subheader("🕐 Reclamações Recentes")

# Ordena por data mais recente e mostra as 10 primeiras
reclamacoes_recentes = df_filtrado.sort_values("data_reclamacao", ascending=False).head(10)

# Formata as colunas para exibição
display_cols = ["empresa", "titulo", "data_reclamacao"]
if "status" in df_filtrado.columns:
    display_cols.append("status")

st.dataframe(
    reclamacoes_recentes[display_cols],
    column_config={
        "empresa": st.column_config.TextColumn("🏢 Empresa", width="medium"),
        "titulo": st.column_config.TextColumn("📝 Título", width="large"),
        "data_reclamacao": st.column_config.DatetimeColumn("📅 Data", format="DD/MM/YYYY"),
        "status": st.column_config.TextColumn("📋 Status", width="small"),
    },
    hide_index=True,
    use_container_width=True,
)

# Footer
st.markdown("---")
st.markdown(f"📊 **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("*Dados coletados automaticamente do Reclame AQUI*")

# Botão de refresh
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
