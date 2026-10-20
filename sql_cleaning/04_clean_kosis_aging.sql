-- [한국] 고령인구비율 원자료 정제 (raw_kosis_aging -> cleaned_kosis_aging)
-- 정제 규칙:
--   1) region 컬럼에 17개 시·도뿐 아니라 시·군·구까지 섞여 있어서
--      WHERE region IN (17개 시도 이름)으로 시도 단위만 남긴다
--   2) item(65세이상인구/전체인구/고령인구비율)이 세로로 쌓인 형태를
--      컬럼 3개로 피벗한다 (estat_A와 동일한 방식)

DROP TABLE IF EXISTS cleaned_kosis_aging;

CREATE TABLE cleaned_kosis_aging AS
SELECT
    region AS region_name_kr,
    year,
    MAX(CASE WHEN item = '전체인구(B)' THEN CAST(value AS REAL) END) AS total_pop,
    MAX(CASE WHEN item = '65세이상인구(A)' THEN CAST(value AS REAL) END) AS elderly_pop,
    MAX(CASE WHEN item = '고령인구비율(A÷B×100)' THEN CAST(value AS REAL) END) AS aging_rate_source
FROM raw_kosis_aging
WHERE region IN (
    '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시',
    '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전북특별자치도',
    '전라남도', '경상북도', '경상남도', '제주특별자치도'
)
GROUP BY region, year
ORDER BY region, year;


SELECT COUNT(*) AS 행수 FROM cleaned_kosis_aging;
