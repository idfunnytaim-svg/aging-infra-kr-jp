-- Q1. 한국과 일본의 지역별 고령화율은 최근 몇 년간 어떻게 변화했는가?
-- 국가별 연도별 고령화율 평균/최소/최대 (Page1 선차트 데이터)
SELECT
    r.country,
    d.year,
    ROUND(AVG(f.aging_rate), 2) AS avg_aging_rate,
    ROUND(MIN(f.aging_rate), 2) AS min_aging_rate,
    ROUND(MAX(f.aging_rate), 2) AS max_aging_rate
FROM Fact_RegionStats f
JOIN Dim_Region r ON r.region_id = f.region_id
JOIN Dim_Date d ON d.date_id = f.date_id
GROUP BY r.country, d.year
ORDER BY r.country, d.year;

-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ===
-- country | year | avg_aging_rate | min_aging_rate | max_aging_rate
-- JP | 2015 | 28.31 | 19.74 | 33.92
-- JP | 2016 | 28.98 | 20.36 | 34.75
-- JP | 2017 | 29.6 | 21.07 | 35.64
-- JP | 2018 | 30.09 | 21.62 | 36.49
-- JP | 2019 | 30.5 | 22.16 | 37.27
