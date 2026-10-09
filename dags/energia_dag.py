"""
DAG diária: carga de energia por subsistema (ONS) + bandeiras tarifárias (ANEEL) -> PostgreSQL.

Cada task faz extract -> transform -> load da sua fonte. A carga usa upsert,
então reexecutar a DAG é seguro (idempotente).
"""
from datetime import timedelta

import pendulum
import psycopg2
from airflow.decorators import dag, task

from energia import extract, load, transform
from energia.config import SUBSISTEMAS, db_dsn

DIAS_MAX_ATRASO = 7


@dag(
    dag_id="energia_pipeline",
    schedule="0 9 * * *",  # o ONS publica o dia anterior pela manhã
    start_date=pendulum.datetime(2026, 1, 1, tz="America/Sao_Paulo"),
    catchup=False,
    default_args={"retries": 3, "retry_delay": timedelta(minutes=10)},
    tags=["energia", "ons", "aneel"],
)
def energia_pipeline():
    @task
    def carga_ons(data_interval_end=None) -> int:
        df = transform.transformar_carga(extract.extrair_carga(data_interval_end.year))
        return load.carregar_carga(db_dsn(), df)

    @task
    def bandeiras_aneel() -> int:
        df = transform.transformar_bandeiras(extract.extrair_bandeiras())
        return load.carregar_bandeiras(db_dsn(), df)

    @task
    def checar_qualidade() -> None:
        """Falha se algum subsistema estiver sem dados recentes (fonte parou ou mudou)."""
        with psycopg2.connect(db_dsn()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_subsistema, MAX(data)
                FROM carga_diaria
                GROUP BY id_subsistema
                HAVING MAX(data) >= CURRENT_DATE - %s
                """,
                (DIAS_MAX_ATRASO,),
            )
            em_dia = {linha[0] for linha in cur.fetchall()}
        atrasados = SUBSISTEMAS - em_dia
        if atrasados:
            raise ValueError(f"Sem carga nos últimos {DIAS_MAX_ATRASO} dias: {sorted(atrasados)}")

    [carga_ons(), bandeiras_aneel()] >> checar_qualidade()


energia_pipeline()
