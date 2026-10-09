import pandas as pd
import pytest

from energia.transform import DadosInvalidos, transformar_bandeiras, transformar_carga


def carga_bruta(linhas):
    return pd.DataFrame(
        linhas, columns=["id_subsistema", "nom_subsistema", "din_instante", "val_cargaenergiamwmed"]
    ).astype(str)


def test_carga_converte_tipos_e_arredonda():
    df = transformar_carga(carga_bruta([["SE", "Sudeste/Centro-Oeste", "2026-01-01", "40463.7935"]]))
    linha = df.iloc[0]
    assert str(linha["data"]) == "2026-01-01"
    assert linha["carga_mwmed"] == pytest.approx(40463.794)
    assert list(df.columns) == ["id_subsistema", "subsistema", "data", "carga_mwmed"]


def test_carga_descarta_linhas_invalidas():
    df = transformar_carga(carga_bruta([
        ["N", "Norte", "2026-01-01", "7649.4"],
        ["N", "Norte", "data-ruim", "7000"],      # data inválida
        ["NE", "Nordeste", "2026-01-01", ""],     # valor vazio
        ["S", "Sul", "2026-01-01", "-5"],         # valor negativo
        ["XX", "Outro", "2026-01-01", "100"],     # subsistema desconhecido
    ]))
    assert df["id_subsistema"].tolist() == ["N"]


def test_carga_remove_duplicatas_mantendo_a_ultima():
    df = transformar_carga(carga_bruta([
        ["S", "Sul", "2026-01-01", "100"],
        ["S", "Sul", "2026-01-01", "200"],
    ]))
    assert df["carga_mwmed"].tolist() == [200]


def test_carga_falha_se_formato_mudar():
    with pytest.raises(DadosInvalidos, match="colunas ausentes"):
        transformar_carga(pd.DataFrame({"outra_coluna": ["x"]}))


def test_carga_falha_se_nada_sobrar():
    with pytest.raises(DadosInvalidos, match="nenhuma linha"):
        transformar_carga(carga_bruta([["N", "Norte", "2026-01-01", "0"]]))


def test_bandeiras_converte_decimal_brasileiro():
    bruto = pd.DataFrame({
        "DatGeracaoConjuntoDados": ["2026-10-05"] * 3,
        "DatCompetencia": ["2026-08-01", "2026-09-01", "2026-10-01"],
        "NomBandeiraAcionada": ["Amarela", "Vermelha P2", "Verde"],
        "VlrAdicionalBandeira": ["18,85", "78,77", ",00"],
    })
    df = transformar_bandeiras(bruto)
    assert df["adicional_rs_mwh"].tolist() == [18.85, 78.77, 0.0]
    assert df["bandeira"].tolist() == ["Amarela", "Vermelha P2", "Verde"]
