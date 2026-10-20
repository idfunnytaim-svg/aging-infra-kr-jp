-- 한국+일본을 하나로 합치고(UNION ALL), 양국 모두 결측 없는 2015~2023년만 남긴다.
-- (일본 병상수·요양기관수 원자료가 2023년까지만 있어서, 2024년을 포함하면
--  일본만 인프라 지표가 비어있는 상태가 되어 팀/보고서 요청으로 2023년까지 통일함
--  — docs/원본데이터_점검.md, PROGRESS.md 2026-08-26(5) 참고)

DROP TABLE IF EXISTS combined_all;

CREATE TABLE combined_all AS
SELECT * FROM merged_korea
WHERE year BETWEEN 2015 AND 2023
UNION ALL
SELECT * FROM merged_japan
WHERE year BETWEEN 2015 AND 2023;

-- 검증: 576행 (64개 지역 x 9개년), NULL 없어야 함
SELECT COUNT(*) AS 행수 FROM combined_all;
SELECT COUNT(*) AS NULL있는_행수 FROM combined_all
WHERE total_pop IS NULL OR elderly_pop IS NULL OR medical_beds IS NULL OR care_facility_count IS NULL;
