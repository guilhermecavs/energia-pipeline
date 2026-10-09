# Energia Pipeline — ONS + ANEEL com Airflow

Pipeline de dados que coleta diariamente a **carga de energia elétrica do Brasil** (ONS) e as **bandeiras tarifárias** (ANEEL), carrega tudo num PostgreSQL e cruza as duas fontes para responder: *como o consumo do país se comporta mês a mês e qual bandeira estava vigente?*

Orquestrado com **Apache Airflow**, containerizado com **Docker Compose** e coberto por testes.

## Arquitetura

```
 ┌──────────────────────┐      ┌──────────────── Airflow DAG (diária, 09:00) ────────────────┐
 │ ONS Dados Abertos    │      │                                                              │
 │ carga diária (CSV)   │─────►│  carga_ons ───────┐                                          │
 └──────────────────────┘      │                   ├──► checar_qualidade                      │
 ┌──────────────────────┐      │  bandeiras_aneel ─┘    (falha se algum subsistema            │
 │ ANEEL Dados Abertos  │─────►│                         ficar > 7 dias sem dados)            │
 │ bandeiras (CSV)      │      └───────────────┬──────────────────────────────────────────────┘
 └──────────────────────┘                      │ extract → transform → upsert
                                               ▼
                               ┌───────────────────────────────┐
                               │ PostgreSQL                    │
                               │  carga_diaria                 │
                               │  bandeira_tarifaria           │
                               │  vw_carga_mensal_bandeira     │
                               └───────────────────────────────┘
```

## Fontes de dados

| Fonte | Conjunto | Granularidade |
|---|---|---|
| [ONS](https://dados.ons.org.br/dataset/carga-energia) | Carga de energia por subsistema (N, NE, S, SE/CO), em MWmed | Diária |
| [ANEEL](https://dadosabertos.aneel.gov.br/dataset/bandeiras-tarifarias) | Bandeira tarifária acionada e adicional em R$/MWh | Mensal |

## Decisões de engenharia

- **Idempotência:** a carga usa `INSERT ... ON CONFLICT DO UPDATE`, então reexecutar a DAG ou fazer backfill nunca duplica dados.
- **Validação na transformação:** colunas obrigatórias são conferidas (se a fonte mudar de formato, a task falha com erro claro), e linhas com data inválida, valor vazio/negativo ou subsistema desconhecido são descartadas.
- **Checagem de qualidade:** uma task final verifica se todos os subsistemas têm dados recentes, o que detecta uma fonte que parou de publicar.
- **Lógica separada da orquestração:** o código fica em `src/energia/` e roda com ou sem Airflow (`python -m energia.run`), o que facilita testar.
- **Sem segredos no repositório:** credenciais vêm de `.env` (fora do git); o `.env.example` documenta as variáveis.
- **Constraints no banco:** chave primária composta e `CHECK (carga_mwmed > 0)` como última linha de defesa.

## Como rodar

Pré-requisitos: Docker e Docker Compose.

```bash
cp .env.example .env          # edite a senha
docker compose up -d
```

- Airflow: http://localhost:8080 (usuário `admin`, senha em `docker compose exec airflow cat /opt/airflow/standalone_admin_password.txt`)
- Ative a DAG `energia_pipeline` ou dispare manualmente.

### Sem Airflow

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a && source .env && set +a
PYTHONPATH=src python -m energia.run --ano 2026
```

### Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Exemplo de resultado

```sql
SELECT * FROM vw_carga_mensal_bandeira WHERE mes >= '2026-06-01';
```

| mes | carga_media_sin_mwmed | dias | bandeira | adicional_rs_mwh |
|---|---|---|---|---|
| 2026-06-01 | 75352.4 | 30 | Amarela | 18.85 |
| 2026-07-01 | 76145.0 | 31 | Amarela | 18.85 |
| 2026-08-01 | 80188.7 | 31 | Amarela | 18.85 |
| 2026-09-01 | 82006.6 | 30 | Amarela | 18.85 |
| 2026-10-01 | 83411.4 | 7 | Verde | 0.00 |

## Estrutura

```
├── dags/energia_dag.py       # DAG do Airflow
├── src/energia/
│   ├── extract.py            # download dos CSVs (ONS e ANEEL)
│   ├── transform.py          # limpeza, tipagem e validação
│   ├── load.py               # upsert no PostgreSQL
│   ├── run.py                # execução sem Airflow
│   └── config.py             # URLs e conexão via variáveis de ambiente
├── sql/                      # schema e view (executados na criação do banco)
├── tests/                    # testes da transformação (pytest)
└── docker-compose.yml        # PostgreSQL 16 + Airflow 2.10
```

## Stack

Python · pandas · PostgreSQL · Apache Airflow · Docker · pytest
