-- Q3. 고령화율과 의료 인프라(인구 1만명당 병상수) 사이에는 어떤 관계가 있는가?
-- 양국 모두 의료 인프라 데이터가 있는 최신 연도(2023 — 일본 e-Stat 원자료가
-- 2023년까지만 있음, docs/원본데이터_점검.md 1장 참고) 기준 지역별 산점도 원자료.
SELECT
    r.country,
    r.region_name_kr,
    f.aging_rate,
    ROUND(f.medical_beds_per_10k, 2) AS medical_beds_per_10k
FROM Fact_RegionStats f
JOIN Dim_Region r ON r.region_id = f.region_id
JOIN Dim_Date d ON d.date_id = f.date_id
WHERE d.year = 2023
  AND f.medical_beds_per_10k IS NOT NULL
ORDER BY r.country, f.aging_rate DESC;

-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ===
-- country | region_name_kr | aging_rate | medical_beds_per_10k
-- JP | 아키타현 | 38.840262582056894 | 158.53
-- JP | 고치현 | 36.33633633633634 | 249.16
-- JP | 도쿠시마현 | 35.39568345323741 | 208.55
-- JP | 야마구치현 | 35.36209553158706 | 194.62
-- JP | 야마가타현 | 35.28265107212476 | 136.86
