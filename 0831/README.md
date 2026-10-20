# 0831 공유 — SQL 정제 결과를 실제로 Power BI에 연결

`0828.zip`에서 공유했던 `sql_cleaning/00~17.sql`(원본 CSV를 SQL로 정제·병합·ERD 테이블 조립하는 전체 과정)은 그동안 `data/cleaning_process.db`라는 별도 DB 안에만 있고, 운영 DB(`aging_infra.db`)와 값이 같은지 대조하는 검증 용도로만 쓰였습니다. 즉 "SQL로 정제는 했지만 그 결과를 실제로 Power BI에 넣어 쓰지는 않는" 상태였습니다.

이번에 그 마지막 연결 고리를 추가했습니다 — `sql_cleaning`이 만든 결과 테이블(`Dim_Country`/`Dim_Region`/`Dim_Date`/`Fact_RegionStats`/`Fact_Population`/`Fact_Infra`)을 CSV로 뽑아서(`export_csv_for_powerbi_from_sql.py`), **이제 Power BI에 넣는 CSV가 SQL 정제 결과 그 자체**입니다.

```
원본 CSV → sql_cleaning/*.sql (SQL 정제·병합·ERD 조립, cleaning_process.db)
        → export_csv_for_powerbi_from_sql.py
        → powerbi_export_sql/*.csv
        → Power BI에서 임포트 + 관계 설정 → ERD
```

## 1. `powerbi_export_sql/` — Power BI에 바로 넣는 파일 6개

기존 `팀원공유0826v4`의 `powerbi_export/`(pandas 기준)와 컬럼 구성이 다릅니다 — **이 `0831.zip`은 발표용으로 모든 Fact 테이블이 `Dim_Date`를 정식 FK(`date_id`)로 참조**하도록 만들었습니다. `팀원공유0826v4`나 `data/powerbi_export_sql/`은 여전히 `Fact_Population`/`Fact_Infra`에 `year`(자연키, `Dim_Date` 없이 단독 사용)를 씁니다.

⚠️ **설계가 바뀐 이유**: `Fact_RegionStats.csv`를 `date`(실제 연도값) 대신 `date_id`로 되돌리면서(2026-08-31), 발표 일관성을 위해 `Fact_Population.csv`·`Fact_Infra.csv`도 `date_id`로 맞췄습니다. 그 결과 이 `0831.zip`의 ERD는 원래 "4테이블 스노우플레이크"(`Dim_Date` 없이 `year`를 자연키로 직접 가짐)가 아니라, **`Dim_Date`가 두 ERD 옵션(기본/스노우플레이크) 모두에 공통으로 들어가는 구조**가 됐습니다. `팀원공유0826v4/PowerBI_가이드.md`의 "왜 이렇게 나눴나"(Dim_Date를 별도 테이블로 안 둔 이유) 설명은 이 `0831.zip`에는 더 이상 적용되지 않으니, 발표 때는 아래 사용법을 따로 참고하세요.

| 파일 | 역할 | 키 컬럼 |
|---|---|---|
| `Dim_Country.csv` (2행) | 국가 정보 | country (PK) |
| `Dim_Region.csv` (64행) | 지역 정보 | region_id (PK), country (FK) |
| `Dim_Date.csv` (9행) | 연도 정보 | date_id (PK) |
| `Fact_RegionStats.csv` (576행) | 기본 ERD용 실제 수치 | region_id (FK), date_id (FK) |
| `Fact_Population.csv` (576행) | 스노우플레이크용 인구 지표 | region_id (FK), date_id (FK) ⚠️ 팀원공유0826v4는 `year`(FK 아님) |
| `Fact_Infra.csv` (576행) | 스노우플레이크용 인프라 지표 | region_id (FK), date_id (FK) ⚠️ 팀원공유0826v4는 `year`(FK 아님) |

**Power BI 사용법**:
1. 6개 파일 전부 "가져오기 → 텍스트/CSV"로 불러온다.
2. **모델 보기**로 이동.
3. 기본 ERD를 쓸 거면: `Dim_Region[region_id]`↔`Fact_RegionStats[region_id]`, `Dim_Date[date_id]`↔`Fact_RegionStats[date_id]` 2개만 연결.
4. 스노우플레이크를 쓸 거면: `Dim_Country[country]`↔`Dim_Region[country]`, `Dim_Region[region_id]`↔`Fact_Population[region_id]`, `Dim_Region[region_id]`↔`Fact_Infra[region_id]`, **추가로** `Dim_Date[date_id]`↔`Fact_Population[date_id]`, `Dim_Date[date_id]`↔`Fact_Infra[date_id]` — 총 5개 관계, 5테이블 구조가 됩니다.
5. 두 옵션을 같이 쓰면 `Fact_RegionStats`와 `Fact_Population`/`Fact_Infra`가 같은 데이터를 중복으로 갖게 되니, 발표에서는 하나만 골라 쓰세요.

## 2. 값 검증

운영 DB(`aging_infra.db`, pandas 기준)와 행수·값을 전부 대조했습니다.

- `Dim_Country`·`Dim_Region`·`Dim_Date`·`Fact_Infra`: 완전히 동일
- `Fact_RegionStats`·`Fact_Population`: 소수점 6자리까지는 완전히 동일하고, 그 아래(13~15번째 자리)에서만 미세한 부동소수점 오차가 있습니다(예: `30.761316872427987` vs `...983`). pandas와 SQLite가 같은 나눗셈을 계산하는 순서가 미세하게 달라서 생기는 정상적인 노이즈이며, 실질적인 데이터 차이는 없습니다.

## 3. `export_csv_for_powerbi_from_sql.py`

`Dim_Country`/`Dim_Region`/`Dim_Date`/`Fact_RegionStats`를 만든 스크립트입니다(마스터 버전, `data/powerbi_export_sql/`·`팀원공유0826v4/powerbi_export/`와 동일). 다만 이 폴더의 `Fact_Population.csv`·`Fact_Infra.csv`(`date_id` 버전)는 이 `0831.zip`에서만 쓰는 변형이라 이 스크립트에는 반영돼 있지 않습니다 — `Fact_RegionStats`에서 `region_id, date_id, ...`만 직접 뽑은 별도 쿼리로 만들었습니다.
