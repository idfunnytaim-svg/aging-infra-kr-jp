# 0828 공유 — SQL 정제 과정 + Power BI 꾸미기 가이드

## 1. sql_cleaning/ — 원본 CSV → SQL 정제 → ERD 최종 테이블

기존까지는 데이터 정제(지역 필터링, 항목 정리, 중복 제거, 한/일 병합, 파생컬럼 계산)가 전부 Python(pandas)으로만 되어 있었습니다. 이 폴더는 그 과정을 SQL(SELECT/WHERE/CASE WHEN/GROUP BY/JOIN, 초보자 수준 문법만 사용)로 그대로 재현한 것입니다.

- `00_create_raw_tables.sql` : 원본 CSV 7개를 담을 테이블 + 일본 지역명 한글 매핑표
- `01~07_clean_*.sql` : 원본 → 소스별 1:1 정제 (`data/cleaned/` 폴더와 동일한 결과)
- `08~12` : 한국/일본 정제 데이터 병합 → 연도(2015~2023) 통일 → 고령화율 등 파생컬럼 계산
- `13~17` : 실제 ERD 테이블(`Dim_Country`/`Dim_Region`/`Dim_Date`/`Fact_RegionStats`/`Fact_Population`/`Fact_Infra`) 조립

`cleaning_process.db`가 이 SQL을 전부 실행해서 만든 결과 DB입니다. `build_cleaning_db.py`를 실행하면 원본 CSV부터 이 DB까지 처음부터 다시 만들 수 있습니다 (기존 운영 DB `aging_infra.db`와는 완전히 별개 파일이라 서로 영향 없음).

**검증**: 이 SQL로 만든 결과를 실제 운영 DB(`aging_infra.db`, 지금까지 모든 분석·그래프의 기반)와 값 단위로 전부 대조했고, 576행 전부(국가·지역명·연도·고령화율·인구증감률·병상수·요양기관수 등 모든 지표) 완전히 일치함을 확인했습니다.

**2026-08-31 업데이트**: 이때까지는 이 SQL 정제 결과가 검증 용도로만 쓰이고 실제 Power BI로는 연결되지 않았는데, `0831.zip`에서 그 마지막 연결(SQL 정제 결과 → CSV export → Power BI ERD)을 완성했습니다. 이제 `팀원공유0826v4`의 `powerbi_export/`도 이 SQL 정제 결과 기준으로 교체됐습니다.

## 2. PowerBI_예쁘게_꾸미기_가이드.md + PowerBI_테마_고령화인프라.json

Power BI 그래프를 더 보기 좋게 다듬는 방법을 정리했습니다. 동봉한 테마 파일은 지금까지 만든 Python 그래프(`figures/`, `최종선정그래프/`)와 **완전히 같은 색상**(한국=파랑 `#2a78d6`, 일본=주황 `#eb6834`)으로 만들어서, Power BI에서 바로 적용(보기 → 테마 → 테마 찾아보기)하면 전체 프로젝트의 색이 일관되게 맞춰집니다. 자세한 단계는 가이드 문서를 참고하세요.
