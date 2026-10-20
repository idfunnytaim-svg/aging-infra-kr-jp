-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/08_merge_korea.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 한국 3개 정제 테이블(cleaned_kosis_aging/beds/care)을 region+year 기준으로 합친다
-- 고령인구비율 테이블(total_pop·elderly_pop 있음)을 기준(LEFT)으로 삼고
-- 병상수·요양기관수를 region+year가 같은 행끼리 JOIN해서 붙인다
-- aging_rate_source(KOSIS가 이미 계산해서 제공하는 고령인구비율 값)도 같이
-- 가져온다

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


SELECT COUNT(*) AS 행수 FROM merged_korea;
