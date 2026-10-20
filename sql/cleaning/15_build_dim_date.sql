-- ERD 차원 테이블 조립 3/3: Dim_Date
-- Dim_Region과 같은 방식으로, year 오름차순 순서 그대로 date_id 1~9가 자동 부여됨

DROP TABLE IF EXISTS Dim_Date;

CREATE TABLE Dim_Date (
    date_id  INTEGER PRIMARY KEY,
    year     INTEGER NOT NULL UNIQUE
);

INSERT INTO Dim_Date (year)
SELECT DISTINCT year FROM combined_final ORDER BY year;

-- 검증: 9행 (2015~2023)
SELECT COUNT(*) AS 행수 FROM Dim_Date;
