-- ERD 차원 테이블 조립 1/3: Dim_Country
-- (기획서 2.4~2.6, sql/ddl/create_tables.sql과 동일한 정의 — 정적 값 2행)

DROP TABLE IF EXISTS Dim_Country;

CREATE TABLE Dim_Country (
    country          TEXT PRIMARY KEY,
    country_name_kr  TEXT NOT NULL,
    data_source      TEXT NOT NULL,
    region_count     INTEGER NOT NULL
);

INSERT INTO Dim_Country (country, country_name_kr, data_source, region_count) VALUES
    ('KR', '한국', 'KOSIS(국가데이터처)', 17),
    ('JP', '일본', 'e-Stat(총무성통계국)', 47);

SELECT COUNT(*) AS 행수 FROM Dim_Country;  -- 검증: 2행
