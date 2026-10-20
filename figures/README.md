# figures

matplotlib으로 그린 그래프 27장이다. 그래프 유형을 여러 개 그려보고 팀 논의를 거쳐 최종 10장을 골랐다. 최종 10장은 같은 구성으로 Power BI에서도 만들었다([`powerbi/PowerBI_최종그래프_10종.pdf`](../powerbi/PowerBI_최종그래프_10종.pdf)).

## 최종 선정 10장 (발표 순서)

| 발표 번호 | 파일 | 내용 |
|:---:|---|---|
| 01 | `24_indicators_combined_bar.png` | 국가별 고령화율·병상수·요양기관수 (2023) |
| 02 | `12_slope_aging_change.png` | 2015→2023 고령화율 변화, 주목 지역 9곳 |
| 03 | `20_infra_density_trend.png` | 연도별 인프라 밀도 추이 |
| 04 | `19_play_axis_scatter_filmstrip.png` | 고령화율 × 인프라 밀도, 2015·2018·2023 |
| 05 | `22_region_top10_aging.png` | 지역별 고령화율 TOP10 |
| 06 | `25_medical_care_donut.png` | 국가별 의료 vs 돌봄 인프라 구성비 |
| 07 | `08_infra_gap_ranking.png` | 국가 내 인프라 확충 시급 지역 TOP10 |
| 08 | `23_increase_top5_by_country.png` | 고령화율 증가폭 국가별 TOP5 |
| 09 | `26_infra_gap_top5_combined.png` | 국가별 인프라 격차지수 TOP5 |
| 10 | `14_bump_chart_rank.png` | 고령화율 지역 순위 변화 |

그 밖에 `09_simpsons_paradox_care.png`(심슨의 역설, 개인 보고서 그림1)와 `27_ERD_데이터흐름_강원예시.png`(DB 구조 설명)를 README와 보고서에 사용했다.

## 생성 스크립트

| 파일 번호 | 스크립트 | 비고 |
|---|---|---|
| 01~11 | `scripts/visualize.py` | 기획서 대시보드 와이어프레임(Page 1~3) 기준 1차 그래프 |
| 12~19 | `scripts/visualize_powerbi_ideas.py` | 슬로프·범프·히트맵 등 다른 시각화 유형 시도 |
| 20~23 | `scripts/visualize_feedback_0827_2.py` | 팀원 피드백 반영 수정본 |
| 24~26 | `scripts/visualize_final_selection.py` | 최종 선정에 맞춰 새로 그린 3장 |
| 27 | (스크립트 없음) | DB 구조 설명용으로 따로 그린 그림 |
