-- Q5. 고령화 대비 인프라가 가장 부족하여 향후 확충이 필요한 지역은 어디인가?
-- 인프라 격차지수 = 고령화율 순위 - (의료병상수+요양기관수) 순위 (기획서 1.6, 3.4 DAX 정의 그대로).
-- 두 순위 모두 1등이 "가장 높은 값"이므로, 고령화율은 높은데(순위 숫자가 작음) 인프라는
-- 낮은(순위 숫자가 큼) 지역일수록 지수가 큰 음수가 된다 → ASC 정렬 시 상위가 가장 취약한 지역.
-- ⚠️ 주의: 병상수(수십~수백)와 요양기관수(한 자릿수~수십)는 단위 스케일이 크게 달라
-- 단순 합산은 사실상 병상수 순위에 좌우된다. 기획서 3.4 DAX 정의를 그대로 따랐으며,
-- 필요하면 보고서 작성 시 표준화(z-score) 버전을 별도로 검토한다.
WITH latest AS (
    SELECT
        r.country,
        r.region_name_kr,
        f.aging_rate,
        f.medical_beds_per_10k,
        f.care_facility_per_10k,
        (f.medical_beds_per_10k + f.care_facility_per_10k) AS infra_density
    FROM Fact_RegionStats f
    JOIN Dim_Region r ON r.region_id = f.region_id
    JOIN Dim_Date d ON d.date_id = f.date_id
    WHERE d.year = 2023
      AND f.medical_beds_per_10k IS NOT NULL
      AND f.care_facility_per_10k IS NOT NULL
),
ranked AS (
    SELECT
        country,
        region_name_kr,
        aging_rate,
        ROUND(infra_density, 2) AS infra_density,
        RANK() OVER (ORDER BY aging_rate DESC) AS aging_rank,
        RANK() OVER (ORDER BY infra_density DESC) AS infra_rank
    FROM latest
)
SELECT
    country,
    region_name_kr,
    aging_rate,
    infra_density,
    aging_rank,
    infra_rank,
    (aging_rank - infra_rank) AS infra_gap_index
FROM ranked
ORDER BY infra_gap_index ASC
LIMIT 15;

-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ===
-- country | region_name_kr | aging_rate | infra_density | aging_rank | infra_rank | infra_gap_index
-- JP | 야마가타현 | 35.28265107212476 | 137.88 | 5 | 37 | -32
-- JP | 니가타현 | 33.866415804327374 | 124.25 | 13 | 44 | -31
-- JP | 기후현 | 31.22734334541688 | 106.07 | 27 | 55 | -28
-- JP | 나가노현 | 32.684630738522955 | 117.42 | 21 | 48 | -27
-- JP | 이와테현 | 34.909716251074805 | 145.43 | 8 | 32 | -24
