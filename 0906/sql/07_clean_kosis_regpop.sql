-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/07_clean_kosis_regpop.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- [한국] 주민등록인구현황 원자료 정제 (raw_kosis_regpop -> cleaned_kosis_regpop)
-- 참고: 이 파일은 kosis_고령인구비율의 total_pop과 항목이 중복돼서
--       실제 분석(Fact_RegionStats)에는 쓰지 않는다. 다만 "원본 -> 정제"
--       흔적을 남기기 위해 동일한 규칙(17개 시도 필터 + 항목 선택)으로 정제만 해둔다.

DROP TABLE IF EXISTS cleaned_kosis_regpop;

CREATE TABLE cleaned_kosis_regpop AS
SELECT
    region AS region_name_kr,
    year,
    CASE WHEN value = '-' THEN NULL ELSE CAST(value AS REAL) END AS total_pop
FROM raw_kosis_regpop
WHERE region IN (
    '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시',
    '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전북특별자치도',
    '전라남도', '경상북도', '경상남도', '제주특별자치도'
)
AND item = '총인구수'
ORDER BY region, year;


SELECT COUNT(*) AS 행수 FROM cleaned_kosis_regpop;
