-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/03_clean_estat_J.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- [일본] 복지(장기요양시설) 원자료 정제 (raw_estat_J -> cleaned_estat_J)
-- 정제 규칙:
--   cat01_name에는 "시설수"와 "정원수" 두 항목이 섞여 있는데,
--   이 프로젝트에서 비교할 지표는 "개호노인복지시설 수"이므로 정원수는 버리고
--   시설수(介護老人福祉施設数) 항목만 WHERE로 남긴다

DROP TABLE IF EXISTS cleaned_estat_J;

CREATE TABLE cleaned_estat_J AS
SELECT
    m.region_name_kr,
    r.prefecture AS region_name_local,
    CAST(REPLACE(r.time_name, '年度', '') AS INTEGER) AS year,
    CAST(r.value AS REAL) AS care_facility_count
FROM raw_estat_J AS r
JOIN map_jp_prefecture AS m ON m.prefecture_local = r.prefecture
WHERE r.cat01_name = '介護老人福祉施設数'
ORDER BY m.region_name_kr, year;


SELECT COUNT(*) AS 행수 FROM cleaned_estat_J;
