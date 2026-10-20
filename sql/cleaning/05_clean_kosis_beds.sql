-- [한국] 의료기관 병상수 원자료 정제 (raw_kosis_beds -> cleaned_kosis_beds)
-- 정제 규칙:
--   1) region을 17개 시도로 필터링 (kosis_고령인구비율과 동일한 이유)
--   2) item 중 "총병상수(A)"만 사용 (인구 천명당 환산값 등 다른 항목은 제외)
--   3) 원자료에 결측치가 "-" 문자로 들어있는 경우가 있어 NULL로 바꿔준다

DROP TABLE IF EXISTS cleaned_kosis_beds;

CREATE TABLE cleaned_kosis_beds AS
SELECT
    region AS region_name_kr,
    year,
    CASE WHEN value = '-' THEN NULL ELSE CAST(value AS REAL) END AS medical_beds
FROM raw_kosis_beds
WHERE region IN (
    '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시',
    '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전북특별자치도',
    '전라남도', '경상북도', '경상남도', '제주특별자치도'
)
AND item = '총병상수(A)'
ORDER BY region, year;

-- 검증: 170행 (17개 시도 x 10개년)
SELECT COUNT(*) AS 행수 FROM cleaned_kosis_beds;
