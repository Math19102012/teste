import pandas as pd
import streamlit as st
from .sharepoint_client import GraphClient, normalize_columns


def _client_from_secrets() -> GraphClient:
    s = st.secrets
    return GraphClient(
        tenant_id=s["GRAPH_TENANT_ID"],
        client_id=s["GRAPH_CLIENT_ID"],
        client_secret=s["GRAPH_CLIENT_SECRET"],
    )


@st.cache_data(ttl=60 * 15)
def carregar_sharepoint(
    hostname: str,
    site_path: str,
    list_name: str,
) -> pd.DataFrame:

    client = _client_from_secrets()

    try:
        site_id = client.get_site_id(hostname, site_path)
        list_id = client.get_list_id_by_name(site_id, list_name)

        rows = client.fetch_list_items(site_id, list_id)

        # 🔍 DEBUG (vai aparecer no app)
        st.write("DEBUG - quantidade de registros:", len(rows))

        if not rows:
            st.warning("Nenhum dado retornado do SharePoint.")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = normalize_columns(df)

        # 🔍 DEBUG colunas
        st.write("DEBUG - colunas carregadas:", df.columns.tolist())

        # Garante colunas esperadas
        for col in ["Hora de início", "Qual o seu Curso?", "Qual é o seu período?"]:
            if col not in df.columns:
                df[col] = pd.NA

        # Converte datas
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


def carregar_csv(caminho: str = "data/ingressantes.csv") -> pd.DataFrame:
    return pd.read_csv(caminho)
