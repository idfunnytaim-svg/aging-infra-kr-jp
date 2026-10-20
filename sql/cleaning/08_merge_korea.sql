-- 한국 3개 정제 테이블(cleaned_kosis_aging/beds/care)을 region+year 기준으로 합친다
-- 고령인구비율 테이블(total_pop·elderly_pop 있음)을 기준(LEFT)으로 삼고
-- 병상수·요양기관수를 region+year가 같은 행끼리 JOIN해서 붙인다
-- aging_rate_source(KOSIS가 이미 계산해서 제공하는 고령인구비율 값)도 같이
-- 가져온다 -- 한국은 이 값을 그대로 쓰고(11번 참고), 직접 elderly/total*100으로
-- 재계산하지 않는다 (KOSIS 원자료 자체가 반올림된 값이라 재계산 시 소수점 뒷자리가
-- 미세하게 달라짐 — preprocess_and_load.py도 재계산하지 않고 원자료 값을 그대로 씀)

DROP TABLE IF EXISTS merged_korea;

CREATE TABLE merged_korea AS
SELECT
    'KR' AS country,
    a.region_name_kr,
    NULL AS region_name_local,
    a.year,
    a.total_pop,
    a.elderly_pop,
    b.medical_beds,
    c.care_facility_count,
    a.aging_rate_source
FROM cleaned_kosis_aging AS a
LEFT JOIN cleaned_kosis_beds AS b
    ON b.region_name_kr = a.region_name_kr AND b.year = a.year
LEFT JOIN cleaned_kosis_care AS c
    ON c.region_name_kr = a.region_name_kr AND c.year = a.year;

-- 검증: 170행 (17개 시도 x 10개년), 한국은 세 지표 다 2024년까지 있어서 NULL 없어야 함
SELECT COUNT(*) AS 행수 FROM merged_korea;
