-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/02_clean_estat_I.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- [일본] 의료(병상수) 원자료 정제 (raw_estat_I -> cleaned_estat_I)
-- 정제 규칙:
--   병원 병상수(I5211)와 일반진료소 병상수(I5212) 두 항목을 더해서
--   "총 병상수" 하나로 합친다
--   -> GROUP BY로 prefecture+year를 묶고 SUM으로 두 항목을 합산

DROP TABLE IF EXISTS cleaned_estat_I;

CREATE TABLE cleaned_estat_I AS
SELECT
    m.region_name_kr,
    r.prefecture AS region_name_local,
    CAST(REPLACE(r.time_name, '年度', '') AS INTEGER) AS year,
    SUM(CAST(r.value AS REAL)) AS medical_beds
FROM raw_estat_I AS r
JOIN map_jp_prefecture AS m ON m.prefecture_local = r.prefecture
GROUP BY r.prefecture, year
ORDER BY m.region_name_kr, year;


SELECT COUNT(*) AS 행수 FROM cleaned_estat_I;
