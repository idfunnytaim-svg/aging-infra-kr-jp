-- ERD 차원 테이블 조립 2/3: Dim_Region
-- region_id는 INTEGER PRIMARY KEY로 선언만 하고 INSERT할 때 값을 안 주면
-- SQLite가 SELECT 결과가 나오는 순서대로 1부터 자동으로 번호를 매겨준다
-- (ORDER BY로 country, region_name_kr 순 정렬 -> 그 순서 그대로 region_id가 됨)

DROP TABLE IF EXISTS Dim_Region;

CREATE TABLE Dim_Region (
    region_id          INTEGER PRIMARY KEY,
    country            TEXT NOT NULL,
    region_name_kr     TEXT NOT NULL,
    region_name_local  TEXT,
    FOREIGN KEY (country) REFERENCES Dim_Country(country)
);

INSERT INTO Dim_Region (country, region_name_kr, region_name_local)
SELECT DISTINCT country, region_name_kr, region_name_local
FROM combined_final
ORDER BY country, region_name_kr;

-- 검증: 64행 (한국 17 + 일본 47)
SELECT COUNT(*) AS 행수 FROM Dim_Region;
SELECT country, COUNT(*) AS 지역수 FROM Dim_Region GROUP BY country;
