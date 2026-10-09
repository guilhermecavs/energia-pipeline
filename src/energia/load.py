import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

UPSERT_CARGA = """
    INSERT INTO carga_diaria (id_subsistema, subsistema, data, carga_mwmed)
    VALUES %s
    ON CONFLICT (id_subsistema, data) DO UPDATE
    SET subsistema = EXCLUDED.subsistema,
        carga_mwmed = EXCLUDED.carga_mwmed,
        atualizado_em = now()
"""

UPSERT_BANDEIRAS = """
    INSERT INTO bandeira_tarifaria (competencia, bandeira, adicional_rs_mwh)
    VALUES %s
    ON CONFLICT (competencia) DO UPDATE
    SET bandeira = EXCLUDED.bandeira,
        adicional_rs_mwh = EXCLUDED.adicional_rs_mwh,
        atualizado_em = now()
"""


def _upsert(dsn: str, sql: str, df: pd.DataFrame) -> int:
    linhas = list(df.itertuples(index=False, name=None))
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        execute_values(cur, sql, linhas)
    return len(linhas)


def carregar_carga(dsn: str, df: pd.DataFrame) -> int:
    return _upsert(dsn, UPSERT_CARGA, df[["id_subsistema", "subsistema", "data", "carga_mwmed"]])


def carregar_bandeiras(dsn: str, df: pd.DataFrame) -> int:
    return _upsert(dsn, UPSERT_BANDEIRAS, df[["competencia", "bandeira", "adicional_rs_mwh"]])
