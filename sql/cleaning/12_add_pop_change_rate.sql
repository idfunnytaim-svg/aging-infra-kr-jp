-- 인구증감률(%) = (당해연도 인구 - 전년도 인구) / 전년도 인구 * 100
-- "전년도 인구"가 필요한데, 윈도우함수(LAG) 대신 같은 테이블을
-- year = 당해연도-1 조건으로 자기 자신과 조인(self-join)해서 구한다.
-- 전년도 데이터가 없는 각 지역의 2015년은 prev가 없어서 LEFT JOIN 결과가
-- NULL로 남는다 (pandas의 .shift(1)과 동일한 동작).

DROP TABLE IF EXISTS combined_final;

CREATE TABLE combined_final AS
SELECT
    cur.country,
    cur.region_name_kr,
    cur.region_name_local,
    cur.year,
    cur.total_pop,
    cur.elderly_pop,
    cur.medical_beds,
    cur.care_facility_count,
    cur.aging_rate,
    (cur.total_pop - prev.total_pop) * 100.0 / prev.total_pop AS pop_change_rate,
    cur.medical_beds_per_10k,
    cur.care_facility_per_10k
FROM combined_derived AS cur
LEFT JOIN combined_derived AS prev
    ON prev.region_name_kr = cur.region_name_kr AND prev.year = cur.year - 1;

-- 검증: 576행, pop_change_rate가 NULL인 행은 64개(각 지역 2015년 1개씩)여야 함
SELECT COUNT(*) AS 행수 FROM combined_final;
SELECT COUNT(*) AS 첫해_NULL_행수 FROM combined_final WHERE pop_change_rate IS NULL;
