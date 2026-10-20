-- 일본 3개 정제 테이블(cleaned_estat_A/I/J)을 region+year 기준으로 합친다
-- 인구 테이블(2015~2024, 10개년)을 기준(LEFT)으로 삼는데, 병상수·요양기관수
-- 원자료는 2023년까지만 있어서 2024년 행은 medical_beds/care_facility_count가
-- NULL로 남는다 (이 문제는 다음 단계에서 연도를 2015~2023으로 잘라 해결한다)

DROP TABLE IF EXISTS merged_japan;

CREATE TABLE merged_japan AS
SELECT
    'JP' AS country,
    a.region_name_kr,
    a.region_name_local,
    a.year,
    a.total_pop,
    a.elderly_pop,
    b.medical_beds,
    c.care_facility_count,
    NULL AS aging_rate_source  -- 일본 e-Stat에는 이미 계산된 고령화율 컬럼이 없어서
                                -- 한국처럼 원자료 값을 쓸 수 없다 -> 다음 단계에서
                                -- elderly_pop/total_pop*100으로 직접 계산한다
FROM cleaned_estat_A AS a
LEFT JOIN cleaned_estat_I AS b
    ON b.region_name_kr = a.region_name_kr AND b.year = a.year
LEFT JOIN cleaned_estat_J AS c
    ON c.region_name_kr = a.region_name_kr AND c.year = a.year;


SELECT COUNT(*) AS 행수 FROM merged_japan;
SELECT COUNT(*) AS NULL인_2024년_행수 FROM merged_japan WHERE year = 2024 AND medical_beds IS NULL;
