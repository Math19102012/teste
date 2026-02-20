import time
import typing as t
import requests
import pandas as pd

class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_token()

    def _get_token(self) -> str:
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        response = requests.post(url, data=data)
        response.raise_for_status()

        return response.json()["access_token"]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_site_id(self, hostname: str, site_path: str) -> str:
        url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()

        return response.json()["id"]

    def get_list_id_by_name(self, site_id: str, list_name: str) -> str:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()

        lists = response.json().get("value", [])

        for lst in lists:
            if lst["name"].lower() == list_name.lower():
                return lst["id"]

        raise ValueError(f"Lista '{list_name}' não encontrada.")

    def fetch_list_items(self, site_id: str, list_id: str) -> list:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?$expand=fields"

        all_items = []

        while url:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()

            data = response.json()

            items = data.get("value", [])

            # 🔥 Aqui está o pulo do gato (fields!)
            rows = [item.get("fields", {}) for item in items]
            all_items.extend(rows)

            url = data.get("@odata.nextLink")  # paginação automática

        return all_items


# 🔧 Função para normalizar colunas
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\n", " ")
        .str.replace("\r", " ")
    )

    return df
