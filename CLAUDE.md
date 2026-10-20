# 프로젝트 컨텍스트 (Claude Code 자동 로드 파일)

> 이 파일은 Claude Code가 세션마다 자동으로 읽습니다.
> `[입력 필요]` 부분만 직접 채운 뒤 프로젝트 루트에 두세요.

---

## 1. 프로젝트 개요

- **프로젝트명**: 한·일 지역별 고령화와 의료·돌봄 인프라 격차 분석
- **주제 / 분석 대상**: 한국 17개 시·도 / 일본 47개 도도부현의 고령화율과 의료·돌봄 인프라(병상수·장기요양기관수) 수준 간 관계 분석
- **팀 구성**: 커피팀 (홍성현, 팀원, 팀원)
- **내 역할**: 데이터 전처리
- **기간**: 3주 (하루 4시간 / 총 60시간) — `docs/기획서.md` 참고
- **기술 스택**: Python(pandas) · SQL(SQLite) · Python(matplotlib) — ⚠️ 원래 Power BI였으나 macOS 제약으로 Python 시각화로 대체 (oss_burnout_project와 동일한 사유·선례). DBMS는 SQLite로 확정 (2026-08-24, oss_burnout_project 선례 따름).
- **최종 산출물**: SQL Database · SQL 분석 쿼리 · Python 시각화 대시보드(`figures/`) · 프로젝트 보고서 · 발표자료

## 2. 현재 진행 상태

- [x] 기획서 작성 완료 — `docs/기획서.md` (파이프라인·KPI·ERD·SQL 스키마·Power BI 와이어프레임까지 상세 작성됨. 팀명/팀원 칸은 `[입력 필요]`로 비어 있음)
- [x] 일본 e-Stat 데이터 수집 완료 — `data/raw/estat_A_인구세대_prefecture.csv`(총인구·65세이상인구, **인구추계 기반 2015~2024 매년**), `estat_I_의료_prefecture.csv`(병상수, 2015~2023), `estat_J_복지_prefecture.csv`(개호노인복지시설 정원, 2015~2023), 47도도부현 단위로 집계됨 (`scripts/collect_estat_japan.py`)
- [x] 한국 KOSIS 데이터 수집 완료 — `data/raw/kosis_고령인구비율.csv`, `kosis_장기요양기관현황.csv`, `kosis_의료기관병상수.csv`, `kosis_주민등록인구현황.csv` (`scripts/collect_kosis_korea.py`)
  - `kosis_주민등록인구현황.csv`는 `kosis_고령인구비율.csv`와 총인구 항목이 중복돼 전처리에서는 사용하지 않음(원본 기록용 보존, `docs/원본데이터_점검.md` 2.3 참고).
  - `kosis_의료기관병상수.csv`(DT_1YL20971)는 기획서 2.1에 있었으나 최초 수집에서 누락됐던 항목 — 2026-08-24 (3)에 추가 수집함 (`docs/원본데이터_점검.md` 2.5-1 참고).
- [x] 데이터 전처리 + SQL DB 구축 완료 — `scripts/preprocess_and_load.py` 실행 → `data/aging_infra.db`(SQLite). `Dim_Region`(64=한국17+일본47) · `Dim_Date`(9개년, 2015~2023) · `Fact_RegionStats`(576행) 적재, 값 검증 완료(서울 고령화율 12.6%→18.5%(2023), 전남 2023년 한국 최고령 지역(26.1%), 일본 병상밀도 세계 최고 수준과 일치 등). 인프라 격차지수는 아직 파생 안 함(SQL 분석 단계에서 RANKX 방식으로 산출 예정 — 기획서 3.4 DAX 참고).
  - 2026-08-26(5) 팀/보고서 요청으로 적재 연도를 **2015~2023으로 통일**함(원래 인구는 2024까지 있었으나 일본 인프라만 2023년까지라 전체를 2023년까지로 잘라 결측치를 없앰, `scripts/preprocess_and_load.py`의 `YEARS` 참고). 원본 CSV(`data/raw/`)는 2024년분까지 그대로 보존, 로드 시에만 필터링. 결측은 이제 `pop_change_rate`의 각 지역 첫 연도(2015)뿐.
  - 2026-08-25 팀원 요청으로 `Fact_RegionStats`에 원본 절대값 컬럼 4개(`total_pop`·`elderly_pop`·`medical_beds`·`care_facility_count`) 추가함 — 기존 비율 컬럼(aging_rate 등)은 그대로 유지. 전처리 단계별 로직·컬럼별 수식은 `docs/전처리_로그.md`에 전부 기록됨.
- [x] SQL 분석 완료 — `sql/analysis/q1.sql`~`q5.sql` 작성·실행(`scripts/run_analysis.py`). Q2에서 일본 아키타현이 고령화율·인구감소율 순위 모두 1위로 나와 실제 사실(아키타현은 일본에서 고령화율·인구감소가 가장 심한 현)과 일치함을 확인. Q3~Q5는 양국 모두 인프라 데이터가 있는 2023년 기준.
  - ⚠️ Q5 인프라 격차지수는 기획서 3.4 DAX(병상수+요양기관수 단순합산 순위) 그대로 구현했으나, 두 지표의 단위 스케일이 크게 달라 사실상 병상수 순위에 좌우됨 — 쿼리 주석에 명시, 보고서 단계에서 표준화 버전 검토 필요.
- [x] 시각화 완료 — `scripts/visualize.py` 실행 → `figures/01~11_*.png` (Page1~3 와이어프레임 + 발표 보조 그래프). 데이터 상식과 일치 확인(일본 아키타현 고령화율·인구감소율 1위, 세종특별자치시 최저 고령화율 등). 2026-08-25 팀원 요청으로 국가별 2분할 그래프(07·08번)를 국가색 구분 1개 그래프로 통합함(`PROGRESS.md` 2026-08-25 (4) 참고).
  - ⭐ Insight 후보 발견 2건 (`PROGRESS.md` 2026-08-25 참고): (1) 고령화율×요양기관수 상관계수가 국가 내부(KR +0.74, JP +0.82)와 국가 통합(-0.67)에서 부호가 뒤집힘 — 한/일 "장기요양기관" 정의 범위 차이 때문(Simpson's paradox). (2) 인프라 격차지수를 전역 랭킹으로 하면 일본 고령화율이 전반적으로 높아서 TOP15가 전부 일본으로 쏠림 — `visualize.py`는 국가별(PARTITION BY country) 랭킹으로 바꿔서 시각화.
- [x] 기획서 Page3(Insight 1~3, Action Plan) 작성 완료 — `docs/기획서.md`. 위 Insight 2건 + 신규 발견 1건(한국 고령화 속도가 일본의 약 1.8배, 연 0.72%p vs 0.41%p, 2015~2023 기준) 반영.
- [ ] 보고서 작성 — `docs/기획서.md` 1~3장 + `figures/*.png`를 정리해 최종 산출물로 묶기
- [x] 발표자료 작성 — `presentation/커피팀_발표ppt.pdf`, `presentation/발표 대본.pdf`

## 3. DB 접속 정보

- **DBMS**: SQLite (2026-08-24 확정)
- **데이터베이스명**: 기획서 기준 `aging_infra_db` → SQLite이므로 `data/aging_infra.db`
- **접속 정보**: `.env` 파일 참조 (절대 커밋 금지, 문서에도 쓰지 말 것)

DB를 조회할 때는 `scripts/` 아래에 파이썬 스크립트를 만들어 **실제로 실행**한 뒤 결과를 사용한다.

## 4. 데이터 소스

- **e-Stat API** (`api.e-stat.go.jp`, 일본 총무성 통계국 공식 REST API) — appId는 `.env`의 `ESTAT_APP_ID`
- **KOSIS Open API** (`kosis.kr`, 국가데이터처 공식 API) — apiKey는 `.env`의 `KOSIS_API_KEY`
- 대상 지역: 한국 17개 시·도, 일본 47개 도도부현
- 대상 기간: 2015~2023년 (양국 공통 확보 가능 구간, 2026-08-26(5) 팀/보고서 요청으로 2024→2023 통일, 기획서 1.2)
- 수집 스크립트: `scripts/collect_estat_japan.py`(일본), `scripts/collect_kosis_korea.py`(한국)

## 5. 폴더 구조

> 2026-09-02 GitHub 업로드 대비 정리 — 보고서·발표자료 제작에 실제로 쓸 "최종" 자료
> (`sql_cleaning/`, `powerbi/`, `팀원공유0826v4/`, `0831/`)를 루트로 올리고, 대체된
> 구버전 zip·중간 산출물은 전부 `archive/`로 옮김(삭제 아님, 필요하면 그대로 복구 가능).

```text
.
├── CLAUDE.md                       # 이 파일
├── PROGRESS.md                     # 세션 간 인수인계 로그
├── .env                            # ESTAT_APP_ID, KOSIS_API_KEY (커밋 금지, .gitignore 등록됨)
├── .gitignore
├── requirements.txt                 # pandas, requests, matplotlib
├── sql_cleaning/                    # ★ 전처리 SQL 파이프라인 최종본(00~17번, 18개) — 원 0828/sql_cleaning, 로직은 sql/cleaning과 100% 동일(주석만 팀원이 다듬음)
├── powerbi/                         # ★ Power BI 최종 산출물 — pbix파일/(pbix 6개), 그래프이미지/(팀원이 실제로 그린 스크린샷)
├── 팀원공유0826v4/                   # ★ 팀 공유 스냅샷(v4, 6테이블 powerbi_export 기준) — 보고서·발표자료 재료로 사용
├── 0831/                            # ★ SQL 정제 결과 기준 powerbi_export_sql 스냅샷 — 보고서·발표자료 재료로 사용
├── 개인보고서/                       # 개인 관점 보고서(팀 공동 산출물과 별개) — 보고서_초안_개인.md·보고서_개인_최종.docx
├── 0906/                            # 팀원 발표 대본용 — 데이터수집~DB설계 코드 사본(python/·sql/) + 00_설명.md(Python/SQL 두 갈래 파이프라인을 순서대로 설명). 사본이라 여기 고쳐도 운영 코드엔 반영 안 됨(원본은 scripts/·sql_cleaning/·sql/)
├── docs/
│   ├── 기획서.md                    # ★ 최종 산출 문서 (프로젝트 기획서)
│   ├── 원본데이터_점검.md            # 원본 CSV 점검·문제 해결 기록
│   ├── 데이터출처.md                # 데이터셋별 출처(통계표ID·URL·수집방식) 정리
│   └── 전처리_로그.md               # 원본→정제→최종DB 전 단계 처리 규칙 + 컬럼별 수식 전체 기록
├── scripts/
│   ├── collect_estat_japan.py       # 일본 e-Stat 도도부현별 데이터 수집
│   ├── collect_kosis_korea.py       # 한국 KOSIS 시도별 데이터 수집
│   ├── preprocess_and_load.py       # 전처리 + DB 적재 (완료)
│   ├── export_cleaned_sources.py    # 원본 7개 파일을 1:1 정제해 data/cleaned/에 저장 (완료)
│   ├── export_csv_for_powerbi.py    # (팀 공유 파일에서는 더 이상 안 씀, 2026-08-31부터 아래 _from_sql 버전으로 교체됨)
│   ├── export_csv_for_powerbi_from_sql.py  # sql/cleaning/*.sql이 만든 data/cleaning_process.db에서 CSV export → data/powerbi_export_sql/ (완료, 팀 공유용 powerbi_export/의 실제 출처, 2026-08-31)
│   ├── export_for_powerbi.py        # DB를 region×year 단일 flat CSV로 export → data/aging_infra_flat.csv (완료)
│   ├── run_analysis.py              # sql/analysis/*.sql 실행 + 결과 주석 삽입 (완료)
│   └── visualize.py                 # Python 시각화 (Power BI 대체) — figures/*.png 11장 생성 (완료)
├── data/
│   ├── raw/                         # e-Stat/KOSIS 원본 수집 CSV (7개, 미정제)
│   ├── cleaned/                     # 원본 7개를 1:1 정제한 CSV (ERD/전처리 검증용)
│   ├── aging_infra.db               # SQL DB (완료, Dim_Region/Dim_Date/Fact_RegionStats)
│   ├── aging_infra_flat.csv         # DB를 region×year 단일 flat CSV로 합친 것 (Power BI 간편 임포트용)
│   ├── powerbi_export/              # (pandas DB 기준 원본, 팀 공유 파일에는 더 이상 안 씀)
│   └── powerbi_export_sql/          # sql_cleaning 기준 CSV 6개(Dim_Country/Dim_Region/Dim_Date/Fact_RegionStats/Fact_Population/Fact_Infra) — 팀 공유 powerbi_export/가 이걸로 교체됨, 2026-08-31
├── sql/
│   ├── ddl/create_tables.sql        # 테이블 생성 스크립트 (완료)
│   ├── analysis/                    # 분석 쿼리 q1.sql ~ q5.sql (완료, 실행결과 주석 포함)
│   └── cleaning/                    # sql_cleaning/과 로직 동일한 원본(검증 스크립트 build_cleaning_db.py가 참조하는 경로, 건드리지 않음)
├── figures/                         # 그래프 PNG 26장 (완료, 기획서 Page1~3 와이어프레임 대응)
├── archive/                         # 구버전/대체된 산출물 보관(삭제 아님) — zips/(구버전 zip 12개), 0828_기타/, 0831_power/, 최종선정그래프/, docs_backup/
└── presentation/                    # 발표자료 — 커피팀_발표ppt.pdf, 발표 대본.pdf (완료)
```

## 6. 작업 규칙 (중요)

1. **추측 금지.** `docs/기획서.md`의 빈칸은 실제 DB와 코드에서 **확인한 사실만** 쓴다.
2. 확인할 수 없는 항목은 지어내지 말고 `> ⚠️ 확인 필요: (이유)` 로 남긴다.
3. 사람이 결정해야 하는 항목(팀명, 팀원 이름, DBMS 확정 등)은 `[입력 필요]` 로 남긴다.
4. 문서에 쓰는 **숫자(행 수, 분석 기간, 항목 개수)는 반드시 쿼리 결과를 근거로** 한다.
5. 문서에 쓰는 **테이블명·컬럼명은 실제 DB와 철자까지 일치**해야 한다.
6. SQL을 작성하면 파일로 저장만 하지 말고 **실제로 실행해서 에러 없이 결과가 나오는지 확인**한다.
7. **Power BI `.pbix` 파일은 생성할 수 없다.** oss_burnout_project와 동일하게 Python 시각화로 대체하고, 필요하면 Power BI 설계(모델링·DAX)는 참고용 문서로만 남긴다.
8. 한 번에 기획서 전체를 고치지 말고 **요청받은 장(章)만** 수정한다.
9. 모든 문서는 한국어로 작성한다.
10. 작업을 마치면 `PROGRESS.md`에 무엇을 했고 다음에 뭘 해야 하는지 3줄로 갱신한다.

## 7. 평가 기준 (문서 작성 시 항상 의식할 것)

oss_burnout_project와 같은 kmove 과제 채점 기준을 공유한다.

| 평가 영역 | 배점 | 평가 내용 |
|---|---:|---|
| 문제 정의 | 15 | 문제 및 분석 목적이 명확한가 |
| 데이터 수집/전처리 | 15 | Python으로 데이터를 적절히 처리했는가 |
| SQL/DB 설계 | 15 | ERD, 테이블, 관계가 적절한가 |
| 데이터 분석 | 15 | SQL 및 분석 질문이 적절한가 |
| Power BI | 20 | 모델링, DAX, 시각화가 적절한가 (→ Python 대체 시 시각화 완성도로 평가) |
| Insight | 10 | 단순 차트를 넘어 의미 있는 결과를 도출했는가 |
| 완성도/발표 | 10 | 결과물의 완성도와 발표가 우수한가 |

특히 **Insight(10점)** 는 "고령화율이 몇 % 높다"가 아니라 **"왜 그런가 → 그래서 어떤 지역에 어떤 조치가 필요한가"** 까지 가야 점수가 나온다. oss_burnout_project에서는 "측정 방법(기간 통일)에 따라 결론이 뒤집힌 사례"가 가장 좋은 평가를 받았다 — 이 프로젝트에서도 단순 상관관계 나열보다 **왜 특정 지역이 격차가 큰지에 대한 가설과 검증**을 찾는 것을 목표로 한다.
