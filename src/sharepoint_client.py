import time
import typing as t
import requests
import pandas as pd

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
GRAPH = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._exp: float = 0.0

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._exp - 60:
            return self._token
        resp = requests.post(
            TOKEN_URL.format(tenant_id=self.tenant_id),
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": GRAPH_SCOPE,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._exp = now + int(data.get("expires_in", 3600))
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    # ---- Descoberta de IDs ----
    def get_site_id(self, hostname: str, site_path: str) -> str:
        # site_path ex.: "/sites/IngressantesFECAP"
        url = f"{GRAPH}/sites/{hostname}:/sites{site_path}?$select=id,webUrl"
        r = requests.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()["id"]

    def get_list_id_by_name(self, site_id: str, display_name: str) -> str:
        url = f"{GRAPH}/sites/{site_id}/lists?$select=id,displayName"
        r = requests.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()

        print("===== LISTAS DISPONÍVEIS NO SITE =====")

        for lst in r.json().get("value", []):
            print("LISTA DISPONÍVEL:", lst.get("displayName"))

        raise ValueError(f"Lista '{display_name}' não encontrada no site {site_id}")

    # ---- Itens da lista ----
    def fetch_list_items(
        self,
        site_id: str,
        list_id: str,
        select_fields: t.List[str] | None = None
    ) -> list[dict]:
        items: list[dict] = []
        url = f"{GRAPH}/sites/{site_id}/lists/{list_id}/items?expand=fields"
        while url:
            r = requests.get(url, headers=self._headers(), timeout=60)
            r.raise_for_status()
            data = r.json()
            for it in data.get("value", []):
                fields = it.get("fields", {})
                if select_fields:
                    fields = {k: fields.get(k) for k in select_fields}
                items.append(fields)
            url = data.get("@odata.nextLink")
        return items


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    SharePoint costuma codificar espaços/acentos em nomes internos (ex.: _x0020_, _x00e9_).
    Ajuste o dicionário abaixo conforme os campos reais da sua lista.
    """
    renomear = {
        # Exemplos comuns:
        "Hora_x0020_de_x0020_in_cio": "Hora de início",
        "Hora_x0020_de_x0020_conclus_o": "Hora de conclusão",
        "Qual_x0020_o_x0020_seu_x0020_Curso_x003f_": "Qual o seu Curso?",
        "Qual_x0020__x00e9__x0020_o_x0020_seu_x0020_per_x00ed_odo_x003f_": "Qual é o seu período?",
        # Adicione outros conforme necessário depois de inspecionar as chaves de fields
    }
    cols = {k: v for k, v in renomear.items() if k in df.columns}
    if cols:
        df = df.rename(columns=cols)
    return df


