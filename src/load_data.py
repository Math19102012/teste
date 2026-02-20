import pandas as pd
import streamlit as st
from .sharepoint_client import GraphClient, normalize_columns


# 🔐 Cria o client com base no secrets do Streamlit
def _client_from_secrets() -> GraphClient:
    s = st.secrets
    return GraphClient(
        tenant_id=s["GRAPH_TENANT_ID"],
        client_id=s["GRAPH_CLIENT_ID"],
        client_secret=s["GRAPH_CLIENT_SECRET"],
    )


# 🚀 Função principal que carrega do SharePoint
@st.cache_data(ttl=60 * 15)
def carregar_sharepoint() -> pd.DataFrame:
    try:
        # 🔹 CONFIG CORRETA DO SEU SHAREPOINT
        hostname = "edufecap.sharepoint.com"
        site_path = "/sites/IngressantesFECAP"
        list_name = "2024_1 Pesquisa com Ingressantes da GraduaoFECAP"

        client = _client_from_secrets()

        site_id = client.get_site_id(hostname, site_path)
        list_id = client.get_list_id_by_name(site_id, list_name)

        rows = client.fetch_list_items(site_id, list_id)

        # ⚠️ Se não vier nada
        if not rows:
            st.warning("Nenhum dado retornado da lista do SharePoint.")
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # 🔧 Normaliza colunas
        df = normalize_columns(df)

        # 🔍 DEBUG (MUITO IMPORTANTE)
        st.write("🔎 COLUNAS NORMALIZADAS:")
        st.write(df.columns.tolist())

        # 🔐 Garante colunas mínimas (evita quebra do app)
        colunas_esperadas = [
            "Hora de início",
            "Qual o seu Curso?",
            "Qual é o seu período?"
        ]

        for col in colunas_esperadas:
            if col not in df.columns:
                df[col] = pd.NA

        # 📅 Conversão de data
        if "Hora de início" in df.columns:
            df["Hora de início"] = pd.to_datetime(
                df["Hora de início"],
                errors="coerce",
                dayfirst=True
            )

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados do SharePoint: {e}")
        return pd.DataFrame()


# 📁 (opcional) fallback local
def carregar_csv(caminho: str = "data/ingressantes.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(caminho)
        df = normalize_columns(df)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()
