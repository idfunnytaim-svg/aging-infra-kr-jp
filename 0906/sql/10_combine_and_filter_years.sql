-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/10_combine_and_filter_years.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 한국+일본을 하나로 합치고(UNION ALL), 양국 모두 결측 없는 2015~2023년만 남긴다.
-- (일본 병상수·요양기관수 원자료가 2023년까지만 있어서, 2024년을 포함하면
--  일본만 인프라 지표가 비어있는 상태가 되어 2023년까지 통일함

DROP TABLE IF EXISTS combined_all;

CREATE TABLE combined_all AS
SELECT * FROM merged_korea
WHERE year BETWEEN 2015 AND 2023
UNION ALL
SELECT * FROM merged_japan
WHERE year BETWEEN 2015 AND 2023;

SELECT COUNT(*) AS 행수 FROM combined_all;
SELECT COUNT(*) AS NULL있는_행수 FROM combined_all
WHERE total_pop IS NULL OR elderly_pop IS NULL OR medical_beds IS NULL OR care_facility_count IS NULL;
