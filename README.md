# 한·일 지역별 고령화와 의료·돌봄 인프라 격차 분석

한국 17개 시·도 / 일본 47개 도도부현의 고령화율과 의료·돌봄 인프라(병상수·장기요양기관수)
수준 간 관계를 분석하는 kmove 미니프로젝트입니다. 상세 배경·목적·KPI는
[`docs/기획서.md`](docs/기획서.md) 참고.

## 최종 산출물

| 폴더 | 내용 |
|---|---|
| [`presentation/`](presentation) | 팀 발표자료 — 발표 PPT(`커피팀_발표ppt.pdf`), 발표 대본(`발표 대본.pdf`) |
| [`sql_cleaning/`](sql_cleaning) | 원본 CSV → 정제 → ERD 테이블 조립까지 SQL만으로 구현한 전처리 파이프라인(00~17번, 18개 파일) |
| [`powerbi/`](powerbi) | Power BI 최종 결과물 — `pbix파일/`(실제 pbix), `그래프이미지/`(스크린샷) |
| [`팀원공유0826v4/`](팀원공유0826v4) | 팀 공유 스냅샷(6테이블 `powerbi_export` 기준) — 가이드·데이터사전·전처리 로그 포함 |
| [`0831/`](0831) | SQL 정제 결과(`sql_cleaning/`) 기준 `powerbi_export_sql` 스냅샷 |
| [`개인보고서/`](개인보고서) | 개인 관점 보고서(팀 공동 산출물과 별개, 해석·서술은 개인 저작) |

## 지원 자료

- `docs/` — 기획서, 데이터출처, 데이터사전, 전처리 로그, Power BI 가이드 등 서술형 문서
- `data/` — 원본 CSV(`raw/`), SQL DB(`aging_infra.db`), Power BI export CSV
- `scripts/` — 데이터 수집(e-Stat/KOSIS API)·전처리·분석·시각화 Python 스크립트
- `sql/` — DDL, 분석 쿼리(q1~q5), 정제 파이프라인 원본(`sql_cleaning/`과 로직 동일)
- `figures/` — matplotlib 시각화 26장 (Power BI 대체용, macOS 환경 제약으로 채택)
- `archive/` — 대체된 구버전 zip·중간 산출물 보관용(삭제 아님)

## 데이터 출처

- **e-Stat** (`api.e-stat.go.jp`, 일본 총무성 통계국 공식 API)
- **KOSIS Open API** (`kosis.kr`, 한국 국가데이터처 공식 API)
- 대상 기간: 2015~2023년 (양국 공통 확보 가능 구간)

상세 출처(통계표 ID·URL)는 [`docs/데이터출처.md`](docs/데이터출처.md) 참고.

## DB 재현

```bash
pip install -r requirements.txt
python scripts/collect_estat_japan.py      # 일본 원본 수집
python scripts/collect_kosis_korea.py      # 한국 원본 수집
python scripts/preprocess_and_load.py      # 전처리 + data/aging_infra.db 적재
python scripts/run_analysis.py             # sql/analysis/q1~q5.sql 실행
python scripts/visualize.py                # figures/*.png 생성
```

`.env`에 `ESTAT_APP_ID`·`KOSIS_API_KEY` 필요(커밋 금지, `.gitignore` 등록됨).
