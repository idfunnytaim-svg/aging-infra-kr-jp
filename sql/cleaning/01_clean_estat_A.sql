-- [일본] 인구/세대 원자료 정제 (raw_estat_A -> cleaned_estat_A)
-- 정제 규칙:
--   1) time_name("2015年度")에서 "年度" 글자를 지우고 정수 연도로 변환
--   2) cat01_name(총인구/65세이상인구)이 세로로 쌓인 형태를 컬럼 2개로 피벗
--      (같은 prefecture+year를 하나로 묶고, 항목별로 값을 뽑아냄)
--   3) 일본어 지역명을 map_jp_prefecture로 조인해서 한글 지역명을 붙임

DROP TABLE IF EXISTS cleaned_estat_A;

CREATE TABLE cleaned_estat_A AS
SELECT
    m.region_name_kr,
    r.prefecture AS region_name_local,
    CAST(REPLACE(r.time_name, '年度', '') AS INTEGER) AS year,
    MAX(CASE WHEN r.cat01_name = 'A1101_総人口' THEN CAST(r.value AS REAL) END) AS total_pop,
    MAX(CASE WHEN r.cat01_name = 'A1303_65歳以上人口' THEN CAST(r.value AS REAL) END) AS elderly_pop
FROM raw_estat_A AS r
JOIN map_jp_prefecture AS m ON m.prefecture_local = r.prefecture
GROUP BY r.prefecture, year
ORDER BY m.region_name_kr, year;

-- 검증: data/cleaned/estat_A_인구세대_prefecture.csv와 행 수가 같아야 함 (470행 = 47개현 x 10개년)
SELECT COUNT(*) AS 행수 FROM cleaned_estat_A;
