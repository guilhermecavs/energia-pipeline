CREATE TABLE IF NOT EXISTS carga_diaria (
    id_subsistema  VARCHAR(2)     NOT NULL,
    subsistema     TEXT           NOT NULL,
    data           DATE           NOT NULL,
    carga_mwmed    NUMERIC(12, 3) NOT NULL CHECK (carga_mwmed > 0),
    atualizado_em  TIMESTAMPTZ    NOT NULL DEFAULT now(),
    PRIMARY KEY (id_subsistema, data)
);

CREATE TABLE IF NOT EXISTS bandeira_tarifaria (
    competencia       DATE          PRIMARY KEY,  -- primeiro dia do mês
    bandeira          TEXT          NOT NULL,
    adicional_rs_mwh  NUMERIC(8, 2) NOT NULL,
    atualizado_em     TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Carga média mensal do SIN (soma dos subsistemas) cruzada com a bandeira vigente
CREATE OR REPLACE VIEW vw_carga_mensal_bandeira AS
WITH sin_diario AS (
    SELECT data, SUM(carga_mwmed) AS carga_sin_mwmed
    FROM carga_diaria
    GROUP BY data
    HAVING COUNT(*) = 4  -- só dias com os 4 subsistemas
)
SELECT
    date_trunc('month', s.data)::date      AS mes,
    ROUND(AVG(s.carga_sin_mwmed), 1)       AS carga_media_sin_mwmed,
    COUNT(*)                               AS dias,
    b.bandeira,
    b.adicional_rs_mwh
FROM sin_diario s
LEFT JOIN bandeira_tarifaria b
       ON b.competencia = date_trunc('month', s.data)::date
GROUP BY 1, b.bandeira, b.adicional_rs_mwh
ORDER BY 1;
