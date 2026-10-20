-- ERD 뷰 2개 (sql/ddl/create_tables.sql과 동일 정의)
-- Fact_RegionStats를 인구 지표 / 인프라 지표로 나눠서 보여준다

DROP VIEW IF EXISTS Fact_Population;
DROP VIEW IF EXISTS Fact_Infra;

CREATE VIEW Fact_Population AS
SELECT f.region_id, d.year, f.total_pop, f.elderly_pop, f.aging_rate, f.pop_change_rate
FROM Fact_RegionStats f
JOIN Dim_Date d ON d.date_id = f.date_id;

CREATE VIEW Fact_Infra AS
SELECT f.region_id, d.year, f.medical_beds, f.care_facility_count,
       f.medical_beds_per_10k, f.care_facility_per_10k
FROM Fact_RegionStats f
JOIN Dim_Date d ON d.date_id = f.date_id
WHERE f.medical_beds IS NOT NULL;

SELECT COUNT(*) AS Fact_Population_행수 FROM Fact_Population;  -- 검증: 576행
SELECT COUNT(*) AS Fact_Infra_행수 FROM Fact_Infra;             -- 검증: 576행 (NULL 없음)
