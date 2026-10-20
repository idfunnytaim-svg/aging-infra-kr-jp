-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/06_clean_kosis_care.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- [한국] 장기요양기관 현황 원자료 정제 (raw_kosis_care -> cleaned_kosis_care)
-- 정제 규칙:
--   이 원자료는 region이 이미 17개 시도 + "합계"만 있어서(시군구 없음)
--   region.isin(17개) 필터는 필요 없고, 대신 아래 문제가 있다:
--   category2(시설유형 세부분류: 방문요양/주야간보호/노인요양시설 등)가
--   같은 item명("기관수")으로 세부유형별 행까지 다 들어있어서,
--   그대로 두면 region+year마다 여러 행이 중복으로 나온다.
--   -> category2 = '계'(합계) 행만 남겨서 지역 전체 합산 값 하나만 쓴다.

DROP TABLE IF EXISTS cleaned_kosis_care;

CREATE TABLE cleaned_kosis_care AS
SELECT
    region AS region_name_kr,
    year,
    CASE WHEN value = '-' THEN NULL ELSE CAST(value AS REAL) END AS care_facility_count
FROM raw_kosis_care
WHERE region != '합계'
  AND item = '기관수'
  AND category2 = '계'
ORDER BY region, year;

SELECT COUNT(*) AS 행수 FROM cleaned_kosis_care;
