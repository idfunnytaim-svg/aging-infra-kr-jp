"""Power BI import용 정제 데이터 CSV export.
data/aging_infra.db(SQLite)의 Dim_Region/Dim_Date/Fact_RegionStats를 조인해
region+year 단위 flat wide CSV 한 장으로 만든다. 결측치(일본 2024년 인프라)는
빈 값으로 그대로 둔다 — Power BI에서 결측 처리를 직접 하도록.
"""
import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
OUT_PATH = BASE / "data" / "aging_infra_flat.csv"


def main():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, r.region_name_local, d.year,
               f.total_pop, f.elderly_pop, f.medical_beds, f.care_facility_count,
               f.aging_rate, f.pop_change_rate,
               f.medical_beds_per_10k, f.care_facility_per_10k
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        ORDER BY r.country, r.region_name_kr, d.year
    """).fetchall()
    con.close()

    header = ["country", "region_name_kr", "region_name_local", "year",
              "total_pop", "elderly_pop", "medical_beds", "care_facility_count",
              "aging_rate", "pop_change_rate",
              "medical_beds_per_10k", "care_facility_per_10k"]
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if v is None else v for v in row])

    print(f"완료: {OUT_PATH} ({len(rows)}행)")


if __name__ == "__main__":
    main()
