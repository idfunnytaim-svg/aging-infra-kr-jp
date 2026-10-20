-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/13_build_dim_country.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 최종 테이블 생성(Dim_Country 생성)

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

SELECT COUNT(*) AS 행수 FROM Dim_Country; 