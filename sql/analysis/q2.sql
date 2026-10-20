-- Q2. 고령화율이 높은 지역과 인구감소율이 높은 지역은 일치하는가?
-- 양국 모두 인구 데이터가 있는 최신 연도(Dim_Date의 최댓값) 기준으로 지역별
-- 고령화율 순위(aging_rank)와 인구감소율 순위(pop_decline_rank)를 나란히 비교한다.
-- 상관계수 자체는 이 결과를 Python(pandas .corr())으로 계산한다 — scripts/visualize.py.
WITH latest AS (
    SELECT
        r.country,
        r.region_name_kr,
        f.aging_rate,
        f.pop_change_rate
    FROM Fact_RegionStats f
    JOIN Dim_Region r ON r.region_id = f.region_id
    JOIN Dim_Date d ON d.date_id = f.date_id
    WHERE d.year = (SELECT MAX(year) FROM Dim_Date)
      AND f.pop_change_rate IS NOT NULL
)
SELECT
    country,
    region_name_kr,
    aging_rate,
    ROUND(pop_change_rate, 3) AS pop_change_rate,
    RANK() OVER (ORDER BY aging_rate DESC) AS aging_rank,
    RANK() OVER (ORDER BY pop_change_rate ASC) AS pop_decline_rank
FROM latest
ORDER BY aging_rank;

-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ===
-- country | region_name_kr | aging_rate | pop_change_rate | aging_rank | pop_decline_rank
-- JP | 아키타현 | 38.840262582056894 | -1.72 | 1 | 2
-- JP | 고치현 | 36.33633633633634 | -1.479 | 2 | 5
-- JP | 도쿠시마현 | 35.39568345323741 | -1.278 | 3 | 9
-- JP | 야마구치현 | 35.36209553158706 | -1.142 | 4 | 16
-- JP | 야마가타현 | 35.28265107212476 | -1.441 | 5 | 6
