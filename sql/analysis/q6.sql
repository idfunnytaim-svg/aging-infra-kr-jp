-- Q6. 인프라 격차지수 표준화(z-score) 버전 — Q5의 단위 스케일 문제 보완
-- Q5와 최종 DAX는 인프라 점수를 "1만명당 병상수 + 1만명당 요양기관수"로 단순 합산한다.
-- 병상수는 100 안팎, 요양기관수는 1~6 정도라 합산 점수가 사실상 병상수 순위로 정해진다.
-- 여기서는 두 지표를 각각 국가 안에서 z-score로 바꾼 뒤 평균을 내서, 병상과 요양기관이
-- 같은 비중으로 반영되게 했다. 순위는 최종 DAX와 같이 국가 안에서 매긴다(PARTITION BY country).
-- z = (값 - 국가 평균) / 국가 표준편차(모표준편차). SQRT는 SQLite 3.35+ 수학 함수.
-- infra_gap_raw(단순 합산)와 infra_gap_z(표준화)를 나란히 출력해 순위 변화를 비교한다.
WITH latest AS (
    SELECT
        r.country,
        r.region_name_kr,
        f.aging_rate,
        f.medical_beds_per_10k AS beds,
        f.care_facility_per_10k AS care
    FROM Fact_RegionStats f
    JOIN Dim_Region r ON r.region_id = f.region_id
    JOIN Dim_Date d ON d.date_id = f.date_id
    WHERE d.year = 2023
),
stats AS (
    SELECT
        country,
        AVG(beds) AS beds_mean,
        SQRT(AVG(beds * beds) - AVG(beds) * AVG(beds)) AS beds_sd,
        AVG(care) AS care_mean,
        SQRT(AVG(care * care) - AVG(care) * AVG(care)) AS care_sd
    FROM latest
    GROUP BY country
),
scored AS (
    SELECT
        l.country,
        l.region_name_kr,
        l.aging_rate,
        l.beds + l.care AS infra_raw,
        ((l.beds - s.beds_mean) / s.beds_sd + (l.care - s.care_mean) / s.care_sd) / 2 AS infra_z
    FROM latest l
    JOIN stats s ON s.country = l.country
),
ranked AS (
    SELECT
        country,
        region_name_kr,
        ROUND(aging_rate, 1) AS aging_rate,
        ROUND(infra_z, 2) AS infra_z,
        RANK() OVER (PARTITION BY country ORDER BY aging_rate DESC) AS aging_rank,
        RANK() OVER (PARTITION BY country ORDER BY infra_raw DESC) AS infra_rank_raw,
        RANK() OVER (PARTITION BY country ORDER BY infra_z DESC) AS infra_rank_z
    FROM scored
)
SELECT
    country,
    region_name_kr,
    aging_rate,
    infra_z,
    aging_rank,
    (aging_rank - infra_rank_raw) AS infra_gap_raw,
    (aging_rank - infra_rank_z) AS infra_gap_z
FROM ranked
ORDER BY country DESC, infra_gap_z ASC;

-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ===
-- country | region_name_kr | aging_rate | infra_z | aging_rank | infra_gap_raw | infra_gap_z
-- KR | 강원특별자치도 | 24.0 | -0.21 | 4 | -9 | -7
-- KR | 서울특별시 | 18.5 | -1.07 | 10 | -5 | -5
-- KR | 제주특별자치도 | 17.9 | -1.28 | 11 | -5 | -5
-- KR | 부산광역시 | 22.6 | 0.13 | 5 | 1 | -4
-- KR | 충청북도 | 20.8 | 0.11 | 7 | -4 | -3
