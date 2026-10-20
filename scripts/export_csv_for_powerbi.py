"""Power BI에서 SQLite ODBC 드라이버 없이 바로 불러올 수 있도록
DB의 테이블/뷰를 각각 CSV로 내보낸다.
Power BI Desktop에서는 홈 → 데이터 가져오기 → 텍스트/CSV로 이 파일들을
하나씩 불러온 뒤, 모델 보기에서 관계(ERD)를 잡으면 된다.

Fact_RegionStats.csv는 DB 물리 테이블과 같이 date_id를 그대로 내보낸다.
Power BI DAX 측정값이 Dim_Date[year]로 연도를 거르기 때문에
Fact_RegionStats[date_id] → Dim_Date[date_id] 관계가 필요하다(docs/기획서.md 3.4).
Fact_Population/Fact_Infra는 같은 데이터를 인구/인프라 지표로 나눈 뷰다(docs/기획서.md 2.4).
"""
import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
OUT_DIR = BASE / "data" / "powerbi_export"

TABLES = ["Dim_Country", "Dim_Region", "Dim_Date", "Fact_RegionStats", "Fact_Population", "Fact_Infra"]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    for table in TABLES:
        cur = con.execute(f"SELECT * FROM {table}")
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
