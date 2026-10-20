-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/16_build_fact_regionstats.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 최종 테이블 생성(Fact_RegionStats 생성)
-- combined_final(정제+파생컬럼까지 끝난 데이터)을 Dim_Region·Dim_Date와
-- JOIN해서 region_id·date_id로 바꿔치기한다

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

SELECT COUNT(*) AS 행수 FROM Fact_RegionStats;
