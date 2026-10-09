import pandas as pd

from energia.config import SUBSISTEMAS


class DadosInvalidos(ValueError):
    """Levantada quando a fonte muda de formato ou chega sem dados úteis."""


def _exigir_colunas(df: pd.DataFrame, colunas: list[str], fonte: str) -> None:
    faltando = set(colunas) - set(df.columns)
    if faltando:
        raise DadosInvalidos(f"{fonte}: colunas ausentes {sorted(faltando)}")


def transformar_carga(bruto: pd.DataFrame) -> pd.DataFrame:
    colunas = ["id_subsistema", "nom_subsistema", "din_instante", "val_cargaenergiamwmed"]
    _exigir_colunas(bruto, colunas, "ONS carga")

    df = bruto[colunas].rename(
        columns={
            "nom_subsistema": "subsistema",
            "din_instante": "data",
            "val_cargaenergiamwmed": "carga_mwmed",
        }
    )
    df["id_subsistema"] = df["id_subsistema"].str.strip()
    df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.date
    df["carga_mwmed"] = pd.to_numeric(df["carga_mwmed"], errors="coerce").round(3)

    df = df.dropna(subset=["data", "carga_mwmed"])
    df = df[df["id_subsistema"].isin(SUBSISTEMAS) & (df["carga_mwmed"] > 0)]
    df = df.drop_duplicates(subset=["id_subsistema", "data"], keep="last")

    if df.empty:
        raise DadosInvalidos("ONS carga: nenhuma linha válida após a limpeza")
    return df.sort_values(["data", "id_subsistema"]).reset_index(drop=True)


def transformar_bandeiras(bruto: pd.DataFrame) -> pd.DataFrame:
    colunas = ["DatCompetencia", "NomBandeiraAcionada", "VlrAdicionalBandeira"]
    _exigir_colunas(bruto, colunas, "ANEEL bandeiras")

    df = bruto[colunas].rename(
        columns={
            "DatCompetencia": "competencia",
            "NomBandeiraAcionada": "bandeira",
            "VlrAdicionalBandeira": "adicional_rs_mwh",
        }
    )
    df["competencia"] = pd.to_datetime(df["competencia"], errors="coerce").dt.date
    df["bandeira"] = df["bandeira"].str.strip()
    # A ANEEL usa vírgula decimal e omite o zero à esquerda (",00")
    df["adicional_rs_mwh"] = pd.to_numeric(
        df["adicional_rs_mwh"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df = df.dropna(subset=["competencia", "bandeira", "adicional_rs_mwh"])
    df = df.drop_duplicates(subset=["competencia"], keep="last")

    if df.empty:
        raise DadosInvalidos("ANEEL bandeiras: nenhuma linha válida após a limpeza")
    return df.sort_values("competencia").reset_index(drop=True)
