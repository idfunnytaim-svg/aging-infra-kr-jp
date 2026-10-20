# Power BI 최종 선정 그래프 10종 — 만드는 방법 (`aging_infra_flat.csv` 기준)

팀이 최종 선택한 그래프 10개를 Power BI에서 만드는 방법입니다. 번호는 이 폴더의 `01~10` 파일과
그대로 대응합니다. 데이터는 계속 **`aging_infra_flat.csv`**(`팀원공유0826v4.zip`) 하나만 씁니다.

> ⚠️ 시작 전에 `docs/PowerBI_가이드.md` 0장(파일 불러오기 · `국가명` 조건 열 · 국가별 색 고정)을
> 먼저 끝내두세요.

---

## 01. 국가별 고령화·인프라 지표 (막대, 한·일 통합)

고령화율(%)·병상수(개)·요양기관수(개)는 단위가 완전히 달라 막대 하나에 같이 그리면 왜곡되므로,
**묶은 세로 막대형 차트 3개**(지표별로 하나씩)를 나란히 놓습니다.

| 차트 | X축 | 값 | 필터 |
|---|---|---|---|
| ① 고령화율 | `국가명` | `aging_rate` 평균 | `year`=2023 |
| ② 병상수 | `국가명` | `medical_beds_per_10k` 평균 | `year`=2023 |
| ③ 요양기관수 | `국가명` | `care_facility_per_10k` 평균 | `year`=2023 |

각 차트 서식에서 데이터 레이블 켜고, 색은 0-4대로 한국=파랑/일본=주황 고정. 캔버스에 3개를 가로로 배치.

---

## 02. 연도별 고령화율 변화 (슬로프 차트)

1. **꺾은선형 차트** 클릭
2. X축: `year`, 필터 → "다음 값과 같음" → **2015, 2023** 두 값만 체크
3. 범례: `region_name_kr`
4. 값: `aging_rate` → 평균
5. `region_name_kr` 필터 → "다음 중 하나" → `부산광역시, 강원특별자치도, 울산광역시, 경상북도, 대구광역시, 경상남도, 아오모리현, 아키타현, 세종특별자치시`
6. 데이터 레이블 켜기 (2023 지점에 지역명+값 표시)

---

## 03. 연도별 인프라밀도 추이 (선차트 2개)

1. **꺾은선형 차트** 클릭 (병상수용)
2. X축: `year` (필터 없음, 전체)
3. 범례: `국가명`
4. 값: `medical_beds_per_10k` → 평균
5. 범례 위치는 서식에서 **아래쪽**으로 (값이 우상향이라 위쪽에 두면 선과 겹침)

같은 방식으로 값만 `care_facility_per_10k`로 바꿔서 두 번째 차트 생성.

---

## 04. 고령화율×인프라밀도 관계 (재생축 산점도)

1. **분산형 차트(Scatter chart)** 클릭
2. X축: `aging_rate`
3. Y축: 계산 열 `인프라밀도` (없으면 아래 DAX로 추가)
4. 범례: `국가명`
5. 크기(Size): `total_pop`
6. **재생 축(Play axis)** 필드에 `year` 드래그
7. 왼쪽 아래 ▶ 버튼으로 2015→2023 애니메이션 재생

```DAX
인프라밀도 = aging_infra_flat[medical_beds_per_10k] + aging_infra_flat[care_facility_per_10k]
```

---

## 05. 지역별 고령화율 TOP10

1. **가로 막대형 차트** 클릭
2. Y축: `region_name_kr`
3. 값: `aging_rate` → 평균
4. 범례: `국가명`
5. 필터: `year`=2023, `aging_rate` 필터 추가 → 형식 **상위 N** → 10
6. 축 정렬: `aging_rate` 내림차순

---

## 06. 국가별 의료 vs 돌봄 인프라 구성비 (도넛)

**Power Query에서 열 피벗 해제 먼저** (`docs/PowerBI_가이드.md` 2-3과 동일):
1. **홈 → 데이터 변환**
2. `medical_beds_per_10k`, `care_facility_per_10k` 두 열 Ctrl+클릭으로 선택 → 우클릭 → **선택한 열만 피벗 해제**
3. 새 열 이름을 `지표`, `값`으로 변경 → **닫기 및 적용**

**차트(한국용):**
1. **도넛형 차트(Donut chart)** 클릭
2. 범례: `지표`
3. 값: `값` → **합계**
4. 필터: `country`=KR, `year`=2023
5. 색: 병상수=`#2A78D6`, 요양기관수=`#EDA100`

같은 차트를 복제해서 필터만 `country`=JP로 바꾸면 일본용이 나옵니다. 두 도넛을 나란히 배치.

---

## 07. 국가 내 인프라 확충 시급지역 TOP10

DAX 계산 열 3개가 필요합니다 (`docs/PowerBI_가이드.md` 3-1과 동일):

```DAX
인프라밀도 = aging_infra_flat[medical_beds_per_10k] + aging_infra_flat[care_facility_per_10k]
```

```DAX
고령화율순위_국가내 =
RANKX(
    FILTER(aging_infra_flat, aging_infra_flat[country]=EARLIER(aging_infra_flat[country]) && aging_infra_flat[year]=EARLIER(aging_infra_flat[year])),
    aging_infra_flat[aging_rate], , DESC
)
```

```DAX
인프라순위_국가내 =
RANKX(
    FILTER(aging_infra_flat, aging_infra_flat[country]=EARLIER(aging_infra_flat[country]) && aging_infra_flat[year]=EARLIER(aging_infra_flat[year])),
    aging_infra_flat[인프라밀도], , DESC
)
```

```DAX
인프라격차지수 = aging_infra_flat[고령화율순위_국가내] - aging_infra_flat[인프라순위_국가내]
```

**차트(한국용):** 가로 막대형, Y축=`region_name_kr`, 값=`인프라격차지수`, 필터 `year`=2023 & `country`=KR,
`인프라격차지수` 필터 → **하위 N**=10(가장 음수부터). 같은 차트를 복제해 `country`=JP로 바꾸면 일본용.

---

## 08. 고령화율 증가폭 — 국가별 TOP5

```DAX
증가폭_2015_2023 =
VAR y2023 = CALCULATE(SUM(aging_infra_flat[aging_rate]), aging_infra_flat[year]=2023, ALLEXCEPT(aging_infra_flat, aging_infra_flat[region_name_kr], aging_infra_flat[country]))
VAR y2015 = CALCULATE(SUM(aging_infra_flat[aging_rate]), aging_infra_flat[year]=2015, ALLEXCEPT(aging_infra_flat, aging_infra_flat[region_name_kr], aging_infra_flat[country]))
RETURN y2023 - y2015
```

**차트(한국용):** 가로 막대형, Y축=`region_name_kr`, 값=`증가폭_2015_2023` 평균, 필터 `country`=KR,
`증가폭_2015_2023` 필터 → **상위 N**=5. 복제해서 `country`=JP로 바꾸면 일본용. 두 차트 나란히 배치.

---

## 09. 국가별 인프라격차지수 TOP5 통합 (하나의 차트에)

07번의 `인프라격차지수` 계산 열이 있어야 합니다. 국가별 TOP5만 걸러내는 플래그 열을 하나 더 추가:

```DAX
격차TOP5여부 =
VAR 국가내순위 =
    RANKX(
        FILTER(aging_infra_flat, aging_infra_flat[country]=EARLIER(aging_infra_flat[country]) && aging_infra_flat[year]=EARLIER(aging_infra_flat[year])),
        aging_infra_flat[인프라격차지수], , ASC
    )
RETURN IF(국가내순위 <= 5, 1, 0)
```

**차트:** 가로 막대형, Y축=`region_name_kr`, 값=`인프라격차지수`, 범례=`국가명`,
필터: `year`=2023, `격차TOP5여부`=1. 축 정렬: 오름차순(가장 음수=가장 시급한 지역이 위로).
→ 한국 TOP5 + 일본 TOP5, 총 10개 지역이 격차지수 순서대로 한 차트에 섞여서 나옵니다.

---

## 10. 고령화율 지역 순위 (범프 차트)

측정값 2개가 필요합니다:

```DAX
평균고령화율 = AVERAGE(aging_infra_flat[aging_rate])
```

```DAX
고령화율순위 =
RANKX(ALLSELECTED(aging_infra_flat[region_name_kr]), [평균고령화율], , DESC)
```

**차트:** 꺾은선형, X축=`year`, 범례=`region_name_kr`, 값=`[고령화율순위]`(원본 aging_rate 아님!),
필터: 02번과 동일한 9개 지역. 서식 → Y축 → **값 반전(Invert)** 켜기(1위가 위로).

---

## 체크리스트

| # | 그래프 | 차트 종류 | DAX 필요 |
|---|---|---|---|
| 01 | 국가별 지표 통합 막대 | 묶은 세로 막대 ×3 | 없음 |
| 02 | 연도별 고령화율(슬로프) | 꺾은선형 | 없음 |
| 03 | 연도별 인프라밀도 | 꺾은선형 ×2 | 없음 |
| 04 | 재생축 산점도 | 분산형+재생축 | 계산 열 1개 |
| 05 | 고령화율 TOP10 | 가로 막대 | 없음 |
| 06 | 의료vs돌봄 구성비 | 도넛 ×2 | 없음 (피벗 해제 필요) |
| 07 | 인프라확충 시급 TOP10 | 가로 막대 ×2 | 계산 열 3개 |
| 08 | 증가폭 국가별 TOP5 | 가로 막대 ×2 | 계산 열 1개 |
| 09 | 격차지수 TOP5 통합 | 가로 막대 ×1 | 계산 열 2개(07 재사용+1) |
| 10 | 지역순위(범프) | 꺾은선형 | 측정값 2개 |
