-- 파생컬럼 계산 (기획서 1.6 핵심 KPI 산출식 그대로)
--   고령화율(%) = elderly_pop / total_pop * 100
--     단, 한국은 KOSIS가 이미 계산해서 제공한 값(aging_rate_source)을 그대로 쓴다
--     (직접 재계산하면 KOSIS 원자료 자체의 반올림 때문에 소수점 뒷자리가 미세하게
--     달라짐 -- preprocess_and_load.py도 한국은 재계산하지 않고 원자료 값을 그대로 씀).
--     일본은 e-Stat에 이런 컬럼이 없어서 직접 계산한다.
--   인구 1만명당 병상수 = medical_beds / (total_pop/10000)
--   인구 1만명당 요양기관수 = care_facility_count / (total_pop/10000)
-- 인구증감률은 "전년도 값"이 필요해서 다음 단계(12번)에서 자기 자신과
-- JOIN해서 따로 계산한다 (여기서는 아직 계산하지 않음)

DROP TABLE IF EXISTS combined_derived;

CREATE TABLE combined_derived AS
SELECT
    country,
    region_name_kr,
    region_name_local,
    year,
    total_pop,
    elderly_pop,
    medical_beds,
    care_facility_count,
    CASE WHEN country = 'KR' THEN aging_rate_source
         ELSE elderly_pop * 100.0 / total_pop END AS aging_rate,
    medical_beds / (total_pop / 10000.0) AS medical_beds_per_10k,
    care_facility_count / (total_pop / 10000.0) AS care_facility_per_10k
FROM combined_all;

SELECT COUNT(*) AS 행수 FROM combined_derived;  -- 검증: 576행
