"""Executa o pipeline sem Airflow: python -m energia.run --ano 2026"""
import argparse
import logging
from datetime import date

from energia import extract, load, transform
from energia.config import db_dsn

log = logging.getLogger("energia")


def executar(ano: int) -> None:
    dsn = db_dsn()

    carga = transform.transformar_carga(extract.extrair_carga(ano))
    log.info("carga: %d linhas carregadas (%s a %s)",
             load.carregar_carga(dsn, carga), carga["data"].min(), carga["data"].max())

    bandeiras = transform.transformar_bandeiras(extract.extrair_bandeiras())
    log.info("bandeiras: %d linhas carregadas", load.carregar_bandeiras(dsn, bandeiras))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, default=date.today().year)
    executar(parser.parse_args().ano)
