import os

ONS_CARGA_URL = (
    "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/carga_energia_di/"
    "CARGA_ENERGIA_{ano}.csv"
)
ANEEL_BANDEIRAS_URL = (
    "https://dadosabertos.aneel.gov.br/dataset/7f43a020-6dc5-44b8-80b4-d97eaa94436c/"
    "resource/0591b8f6-fe54-437b-b72b-1aa2efd46e42/download/bandeira-tarifaria-acionamento.csv"
)

SUBSISTEMAS = {"N", "NE", "S", "SE"}
HTTP_TIMEOUT = 60


def db_dsn() -> str:
    """Monta a string de conexão a partir de variáveis de ambiente (ver .env.example)."""
    return (
        f"host={os.environ.get('ENERGIA_DB_HOST', 'localhost')} "
        f"port={os.environ.get('ENERGIA_DB_PORT', '5432')} "
        f"dbname={os.environ.get('ENERGIA_DB_NAME', 'energia')} "
        f"user={os.environ['ENERGIA_DB_USER']} "
        f"password={os.environ['ENERGIA_DB_PASSWORD']}"
    )
