-- ============================================================
-- [0906 설명용 사본] 원본: sql/ddl/create_tables.sql (DB 설계 원본)
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 한·일 지역별 고령화·인프라 격차 분석 — 테이블 정의 (SQLite)
-- 기획서 2.4~2.6 스키마 그대로 구현.
-- Dim_Country/Fact_Population/Fact_Infra는 2026-08-26 추가 — Power BI ERD를
-- 스노우플레이크 구조로 확장하기 위함(docs/기획서.md 2.4~2.6 및
-- docs/PowerBI_가이드.md 6장 참고). Fact_RegionStats는 그대로 두고
-- Fact_Population/Fact_Infra는 그 위에 얹는 VIEW라 기존 SQL 분석
-- (sql/analysis/q1~q5.sql)과 scripts/visualize.py는 영향받지 않는다.
-- 2026-08-26(2): Power BI에 보여줄 모델을 4테이블로 다듬음 —
-- ① Dim_Country.region_count는 COUNT(Dim_Region)으로 유도되는 값이라 저장 안 함(파생값 중복 저장 금지).
-- ② Dim_Date는 date_id·year 2컬럼뿐이라 부가 속성이 없는 얇은 차원이라 Power BI 모델에서는 제외.
--    Fact_Population/Fact_Infra 뷰가 date_id 대신 year를 자연키로 직접 갖는다.
--    (Dim_Date 테이블 자체는 Fact_RegionStats·q1~q5.sql·visualize.py가 여전히 쓰므로 DB에는 그대로 둔다.)
-- 2026-08-26(3): 팀원 리뷰 반영 — ① Dim_Country.region_count를 다시 추가(팀원 요청, 이전 버전으로 되돌림).
--    ② Fact_RegionStats.csv를 Power BI로 내보낼 때 date_id 대신 실제 연도값을 담은 date 컬럼을
--    쓰도록 export 단계(scripts/export_csv_for_powerbi.py)에서 변환한다. DB 내부의 Fact_RegionStats
--    테이블 자체(및 date_id, q1~q5.sql·visualize.py가 쓰는 부분)는 그대로 유지.

DROP VIEW IF EXISTS Fact_Population;
DROP VIEW IF EXISTS Fact_Infra;
DROP TABLE IF EXISTS Fact_RegionStats;
DROP TABLE IF EXISTS Dim_Region;
DROP TABLE IF EXISTS Dim_Date;
DROP TABLE IF EXISTS Dim_Country;

CREATE TABLE Dim_Country (
    country              TEXT PRIMARY KEY CHECK (country IN ('KR', 'JP')),
    country_name_kr      TEXT NOT NULL,        -- 한국 / 일본
    data_source          TEXT NOT NULL,        -- 데이터 출처 기관
    region_count         INTEGER NOT NULL      -- 소속 지역 수(한국 17 / 일본 47)
);

INSERT INTO Dim_Country (country, country_name_kr, data_source, region_count) VALUES
    ('KR', '한국', 'KOSIS(국가데이터처)', 17),
    ('JP', '일본', 'e-Stat(총무성통계국)', 47);

CREATE TABLE Dim_Region (
    region_id          INTEGER PRIMARY KEY,
    country             TEXT NOT NULL CHECK (country IN ('KR', 'JP')),
    region_name_kr       TEXT NOT NULL,        -- 한국: 시도명 / 일본: 도도부현 한글표기
    region_name_local    TEXT,                 -- 일본만 사용(현지어 표기), 한국은 NULL
    FOREIGN KEY (country) REFERENCES Dim_Country(country)
);

CREATE TABLE Dim_Date (
    date_id  INTEGER PRIMARY KEY,
    year      INTEGER NOT NULL UNIQUE
);

CREATE TABLE Fact_RegionStats (
    region_id              INTEGER NOT NULL,
    date_id                INTEGER NOT NULL,
    total_pop               REAL,               -- 총인구(명) — 원본 절대값
    elderly_pop              REAL,               -- 65세이상인구(명) — 원본 절대값
    medical_beds             REAL,               -- 의료기관 병상수(개) — 원본 절대값
    care_facility_count      REAL,               -- 장기요양(개호) 기관수(개) — 원본 절대값
    aging_rate              REAL,               -- 고령화율(%) = elderly_pop/total_pop*100
    pop_change_rate         REAL,               -- 전년 대비 인구증감률(%), 각 지역 첫 연도는 NULL
    medical_beds_per_10k    REAL,               -- 인구 1만명당 의료기관 병상수 = medical_beds/(total_pop/10000)
    care_facility_per_10k   REAL,               -- 인구 1만명당 장기요양(개호) 기관수 = care_facility_count/(total_pop/10000)
    PRIMARY KEY (region_id, date_id),
    FOREIGN KEY (region_id) REFERENCES Dim_Region(region_id),
    FOREIGN KEY (date_id) REFERENCES Dim_Date(date_id)
);

-- Fact_RegionStats를 인구 지표 / 인프라 지표로 분리한 뷰.
-- 인구 지표(total_pop 등)는 2015~2024 전 지역이 항상 채워지지만,
-- 인프라 지표(medical_beds 등)는 일본이 2023년까지만 있어 2024년 47행이 NULL이다.
-- 그래서 Fact_Infra는 medical_beds가 있는 행만 남겨 NULL 없는 뷰로 만든다.
-- date_id 대신 Dim_Date.year를 그대로 뽑아서(자연키) Power BI 모델에서
-- Dim_Date 테이블 없이도 연도별 필터링·차트가 가능하게 한다.
CREATE VIEW Fact_Population AS
SELECT f.region_id, d.year, f.total_pop, f.elderly_pop, f.aging_rate, f.pop_change_rate
FROM Fact_RegionStats f
JOIN Dim_Date d ON d.date_id = f.date_id;

CREATE VIEW Fact_Infra AS
SELECT f.region_id, d.year, f.medical_beds, f.care_facility_count,
       f.medical_beds_per_10k, f.care_facility_per_10k
FROM Fact_RegionStats f
JOIN Dim_Date d ON d.date_id = f.date_id
WHERE f.medical_beds IS NOT NULL;
