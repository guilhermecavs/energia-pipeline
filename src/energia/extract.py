import io

import pandas as pd
import requests

from energia.config import ANEEL_BANDEIRAS_URL, HTTP_TIMEOUT, ONS_CARGA_URL


def _baixar_csv(url: str) -> pd.DataFrame:
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    # dtype=str: a conversão de tipos fica toda no transform, onde é testada
    return pd.read_csv(io.BytesIO(resp.content), sep=";", dtype=str, encoding="utf-8")


def extrair_carga(ano: int) -> pd.DataFrame:
    """Carga de energia diária por subsistema (ONS) do ano informado."""
    return _baixar_csv(ONS_CARGA_URL.format(ano=ano))


def extrair_bandeiras() -> pd.DataFrame:
    """Histórico mensal de bandeiras tarifárias acionadas (ANEEL)."""
    return _baixar_csv(ANEEL_BANDEIRAS_URL)
