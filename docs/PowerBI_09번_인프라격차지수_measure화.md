# Power BI 09번 그래프(인프라 격차지수 TOP5 통합) — 계산된 열 → measure 전환

`최종선정그래프/09_국가별_인프라격차지수_TOP5_통합.png`를 Power BI 네이티브(DAX)로 재현하는 방법입니다.
기존 `docs/PowerBI_가이드.md` 3-1절의 계산된 열(Column) 방식이 값이 이상하게 나와서, 전부 측정값
(Measure)으로 옮긴 버전입니다. 08번(TOP10)과 같은 measure 세트를 공유하고, TOP N 기준만 다릅니다.

> ⚠️ 시작 전에 `docs/PowerBI_가이드.md`의 0장(파일 불러오기, `국가명` 열, 국가별 색 고정)이 끝나 있어야
> 합니다.

---

## 왜 계산된 열 대신 measure로 옮기나

08·09·10번처럼 "순위(rank)"가 들어가는 계산은 **"지금 화면에 어떤 연도·어떤 나라가 보이는지"에 따라
값이 계속 달라져야** 하는데, 계산된 열은 데이터 새로고침 시 딱 한 번만 고정된 값으로 계산됩니다.
`EARLIER`/`ALLSELECTED` 같은 컨텍스트 함수를 계산된 열 안에서 쓰면 의도와 다르게 동작하는 경우가
많습니다 (10번 범프 차트에서 순위가 전부 1로 뜨던 것과 같은 종류의 문제). 측정값(Measure)은 시각화에
올라갈 때마다 그 시점의 필터 상태를 실시간으로 읽기 때문에 이런 계산에 훨씬 안전합니다.

---

## 1. 기존 계산된 열 삭제

필드 창에서 아래 열들을 우클릭 → 삭제 (있는 것만):

```
인프라밀도, 고령화율순위_국가내, 인프라순위_국가내, 인프라격차지수, 격차TOP5여부
```

---

## 2. 새 측정값 6개 (이 순서대로 만들기)

`평균고령화율`은 10번(범프 차트) 작업에서 이미 만들었으면 재사용, 없으면 같이 추가하세요.

```dax
평균고령화율 = AVERAGE(aging_infra_flat[aging_rate])
```

```dax
평균인프라밀도 =
AVERAGE(aging_infra_flat[medical_beds_per_10k]) + AVERAGE(aging_infra_flat[care_facility_per_10k])
```

```dax
고령화율순위_국가내 =
RANKX(
    FILTER(
        ALLSELECTED(aging_infra_flat),
        aging_infra_flat[country] = SELECTEDVALUE(aging_infra_flat[country]) &&
        aging_infra_flat[year] = SELECTEDVALUE(aging_infra_flat[year])
    ),
    [평균고령화율],
    ,
    DESC
)
```

```dax
인프라순위_국가내 =
RANKX(
    FILTER(
        ALLSELECTED(aging_infra_flat),
        aging_infra_flat[country] = SELECTEDVALUE(aging_infra_flat[country]) &&
        aging_infra_flat[year] = SELECTEDVALUE(aging_infra_flat[year])
    ),
    [평균인프라밀도],
    ,
    DESC
)
```

```dax
인프라격차지수 = [고령화율순위_국가내] - [인프라순위_국가내]
```

```dax
격차순위_국가내 =
RANKX(
    FILTER(
        ALLSELECTED(aging_infra_flat),
        aging_infra_flat[country] = SELECTEDVALUE(aging_infra_flat[country]) &&
        aging_infra_flat[year] = SELECTEDVALUE(aging_infra_flat[year])
    ),
    [인프라격차지수],
    ,
    ASC
)
```

```dax
격차TOP5여부 = IF([격차순위_국가내] <= 5, 1, 0)
```

값이 **더 음수일수록** "고령화율은 상위권인데 인프라는 하위권" = 그 나라 안에서 인프라 확충이
시급한 지역입니다.

### 수식 읽는 법

`SELECTEDVALUE(country)` / `SELECTEDVALUE(year)`가 "지금 이 막대(=지역 하나)가 어느 나라, 어느
연도인지"를 실시간으로 읽어오고, `FILTER(ALLSELECTED(...), ...)`가 그 나라·그 연도 안의 지역들만
모아서 그 안에서만 순위를 매깁니다. 계산된 열에서 쓰던 `EARLIER`는 계산된 열 문법이라 measure에서는
못 쓰고, 대신 measure 세계에서는 `SELECTEDVALUE`가 같은 역할을 합니다.

---

## 3. 차트 만들기

1. **가로 막대형 차트** 클릭
2. Y축: `region_name_kr`
3. 값: `[인프라격차지수]`
4. 범례: `국가명` (한국/일본 색 자동 구분 — 없으면 `docs/PowerBI_가이드.md` 0-3·0-4 참고)
5. 시각적 개체 **필터**: `year` = 2023 (★ 필수 — `SELECTEDVALUE(year)`가 값을 가지려면 연도가
   하나로 고정돼야 함)
6. 시각적 개체 **필터**: `[격차TOP5여부]` 추가 → 값 = 1 인 것만 (한국 TOP5 + 일본 TOP5가 자동으로
   같이 뽑힘)
7. 정렬: `인프라격차지수` 오름차순 (가장 음수 = 가장 시급한 지역이 위로 오도록)

---

## 참고 — 08번(TOP10)과의 관계

08번(`08_고령화율_증가폭_국가별TOP5.png`가 아니라 `07_국가내_인프라확충_시급지역_TOP10.png`)도 같은
measure 세트를 그대로 쓰고, `격차순위_국가내 <= 5` 대신 `<= 10`으로만 바꾸면 됩니다. 즉 위 6개
measure는 08·09번 공통이고, TOP N 기준(5 또는 10)만 필터에서 다르게 걸면 됩니다.

⚠️ `year` 필터를 빼먹으면 `SELECTEDVALUE(year)`가 빈 값(BLANK)이 되어 결과가 전부 공백으로 나올 수
있습니다.
