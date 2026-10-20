"""sql_cleaning(SQL로 정제·조립한 data/cleaning_process.db)의 ERD 테이블을
Power BI에서 바로 불러올 수 있도록 각각 CSV로 내보낸다.

export_csv_for_powerbi.py(운영 DB aging_infra.db 기준)와 쿼리·구조는
동일하되 DB_PATH만 cleaning_process.db로 바꾼 것 — 두 DB는 값까지 100%
일치가 검증돼 있으므로(scripts/build_cleaning_db.py) 결과 CSV도 동일하다.
차이는 "SQL로 정제한 결과가 직접 Power BI로 나간다"는 것뿐이다.

Dim_Date도 내보낸다 — "기본 ERD(3테이블: Dim_Region+Dim_Date+Fact_RegionStats)"
옵션을 계속 지원하기 위해서다(2026-08-31 사용자 결정, 스노우플레이크 전용으로
통일하려던 걸 되돌림). 스노우플레이크(4테이블) 모델을 쓸 때는 그냥 이 파일을
안 쓰면 된다.

Fact_RegionStats는 date_id를 그대로 내보낸다(2026-08-31 재결정) — 예전에는
발표할 때 "왜 date_id가 아니라 실제 연도값을 쓰는지" 설명이 추가로 필요해서
Dim_Date와 조인해 연도값(date)으로 바꿔 내보냈는데, 그러면 정식 FK 관계라는
게 한눈에 안 보여서 다시 date_id로 되돌렸다. Dim_Date[date_id]와 그대로
연결하면 되므로 JOIN도 필요 없어졌다.
"""
import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "cleaning_process.db"
OUT_DIR = BASE / "data" / "powerbi_export_sql"

QUERIES = {
    "Dim_Country": "SELECT * FROM Dim_Country",
    "Dim_Region": "SELECT * FROM Dim_Region",
    "Dim_Date": "SELECT * FROM Dim_Date",
    "Fact_RegionStats": "SELECT * FROM Fact_RegionStats",
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
