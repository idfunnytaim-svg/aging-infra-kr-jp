"""Power BI에서 SQLite ODBC 드라이버 없이 바로 불러올 수 있도록
DB의 테이블/뷰를 각각 CSV로 내보낸다.
Power BI Desktop에서는 홈 → 데이터 가져오기 → 텍스트/CSV로 이 파일들을
하나씩 불러온 뒤, 모델 보기에서 관계(ERD)를 잡으면 된다.

Dim_Country/Fact_Population/Fact_Infra는 Fact_RegionStats를 국가 차원과
인구/인프라 지표로 나눈 스노우플레이크 버전(docs/PowerBI_가이드.md 6장 참고).
기존 Fact_RegionStats.csv도 호환을 위해 계속 내보내지만, 둘을 같은 Power BI
파일에 함께 불러오면 관계가 중복돼 헷갈리므로 한쪽만 골라 쓸 것.

Fact_RegionStats.csv는 2026-08-26(3) 팀원 리뷰 반영 — date_id(1~10 순번) 대신
실제 연도값을 담은 date 컬럼(2015~2024)으로 내보낸다. DB 내부의 Fact_RegionStats
테이블 자체는 date_id를 그대로 쓰고(q1~q5.sql·visualize.py가 참조), 이 export
단계에서만 Dim_Date와 조인해 date_id를 연도값으로 바꿔치기한다.
"""
import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
OUT_DIR = BASE / "data" / "powerbi_export"

# 테이블명 -> (CSV 파일명, 실행할 쿼리). 기본은 SELECT * FROM {table}이고,
# Fact_RegionStats만 date_id를 실제 연도값(date)으로 바꾸는 쿼리를 따로 쓴다.
QUERIES = {
    "Dim_Country": "SELECT * FROM Dim_Country",
    "Dim_Region": "SELECT * FROM Dim_Region",
    "Dim_Date": "SELECT * FROM Dim_Date",
    "Fact_RegionStats": """
        SELECT f.region_id, d.year AS date,
               f.total_pop, f.elderly_pop, f.medical_beds, f.care_facility_count,
               f.aging_rate, f.pop_change_rate, f.medical_beds_per_10k, f.care_facility_per_10k
        FROM Fact_RegionStats f
        JOIN Dim_Date d ON d.date_id = f.date_id
    """,
    "Fact_Population": "SELECT * FROM Fact_Population",
    "Fact_Infra": "SELECT * FROM Fact_Infra",
}


def main():
    OUT_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    for table, query in QUERIES.items():
        cur = con.execute(query)
        headers = [d[0] for d in cur.description]
        rows = cur.fetchall()
        out_path = OUT_DIR / f"{table}.csv"
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(["" if v is None else v for v in row] for row in rows)
        print(f"{table}: {len(rows)}행 -> {out_path}")
    con.close()


if __name__ == "__main__":
    main()
