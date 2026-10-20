-- ============================================================
-- [0906 설명용 사본] 원본: sql_cleaning/15_build_dim_date.sql
-- 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
-- ============================================================

-- 최종 테이블 생성(Dim_Date 생성)
-- Dim_Region과 같은 방식으로, year 오름차순 순서 그대로 date_id 1~9가 자동 부여됨

DROP TABLE IF EXISTS Dim_Date;

CREATE TABLE Dim_Date (
    date_id  INTEGER PRIMARY KEY,
    year     INTEGER NOT NULL UNIQUE
);

INSERT INTO Dim_Date (year)
SELECT DISTINCT year FROM combined_final ORDER BY year;

SELECT COUNT(*) AS 행수 FROM Dim_Date;
