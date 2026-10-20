-- ERD 사실 테이블 조립: Fact_RegionStats
-- combined_final(정제+파생컬럼까지 끝난 데이터)을 Dim_Region·Dim_Date와
-- JOIN해서 region_id·date_id로 바꿔치기한다 (기획서 2.4~2.6, create_tables.sql과 동일 스키마)

DROP TABLE IF EXISTS Fact_RegionStats;

CREATE TABLE Fact_RegionStats (
    region_id              INTEGER NOT NULL,
    date_id                INTEGER NOT NULL,
    total_pop              REAL,
    elderly_pop            REAL,
    medical_beds           REAL,
    care_facility_count    REAL,
    aging_rate             REAL,
    pop_change_rate        REAL,
    medical_beds_per_10k   REAL,
    care_facility_per_10k  REAL,
    PRIMARY KEY (region_id, date_id),
    FOREIGN KEY (region_id) REFERENCES Dim_Region(region_id),
    FOREIGN KEY (date_id) REFERENCES Dim_Date(date_id)
);

INSERT INTO Fact_RegionStats
SELECT
    r.region_id,
    d.date_id,
    f.total_pop,
    f.elderly_pop,
    f.medical_beds,
    f.care_facility_count,
    f.aging_rate,
    f.pop_change_rate,
    f.medical_beds_per_10k,
    f.care_facility_per_10k
FROM combined_final AS f
JOIN Dim_Region AS r ON r.country = f.country AND r.region_name_kr = f.region_name_kr
JOIN Dim_Date AS d ON d.year = f.year;

-- 검증: 576행 (64개 지역 x 9개년)
SELECT COUNT(*) AS 행수 FROM Fact_RegionStats;
