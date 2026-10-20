"""원본 CSV(data/raw/) -> SQL 정제 -> ERD 최종 테이블까지 전 과정을 SQL로 재현
====================================================================

목적: preprocess_and_load.py는 정제(필터링/피벗/중복제거/병합/파생컬럼)를
전부 pandas로 처리해서, "SQL로 데이터를 정제/적재한 흔적"이 코드 어디에도
안 남아있었다. 이 스크립트는 그 로직을 sql/cleaning/*.sql(초보자 수준
SELECT/WHERE/CASE WHEN/GROUP BY/JOIN/self-JOIN만 사용, 윈도우함수·CTE 배제)로
다시 구현해서 "원본 -> 정제 -> ERD(Dim_Country/Dim_Region/Dim_Date/
Fact_RegionStats/Fact_Population/Fact_Infra)"까지 전 과정을 보여주기 위한 것이다.

기존 data/aging_infra.db(분석·시각화가 참조하는 운영 DB)는 절대 건드리지 않고,
완전히 별도의 data/cleaning_process.db에 raw_* -> cleaned_* -> merged_*
-> combined_* -> Dim_*/Fact_* 순서로 테이블을 쌓는다. 마지막에는
aging_infra.db를 ATTACH해서 이 SQL로 만든 Fact_RegionStats가 실제 운영 DB와
값까지 완전히 같은지 직접 대조한다.

실행:
    python3 build_cleaning_db.py
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")
DB_PATH = os.path.join(BASE_DIR, "data", "cleaning_process.db")
PROD_DB_PATH = os.path.join(BASE_DIR, "data", "aging_infra.db")
SQL_DIR = os.path.join(BASE_DIR, "sql", "cleaning")

# raw_* 테이블명 -> 원본 CSV 파일명 (컬럼명은 CSV 헤더와 동일하게 그대로 적재)
RAW_SOURCES = {
    "raw_estat_A": "estat_A_인구세대_prefecture.csv",
    "raw_estat_I": "estat_I_의료_prefecture.csv",
    "raw_estat_J": "estat_J_복지_prefecture.csv",
    "raw_kosis_aging": "kosis_고령인구비율.csv",
    "raw_kosis_beds": "kosis_의료기관병상수.csv",
    "raw_kosis_care": "kosis_장기요양기관현황.csv",
    "raw_kosis_regpop": "kosis_주민등록인구현황.csv",
}

# cleaned_* 테이블 -> 대조할 data/cleaned/ CSV (이미 검증된 결과물)
CLEANED_CHECKS = {
    "cleaned_estat_A": "estat_A_인구세대_prefecture.csv",
    "cleaned_estat_I": "estat_I_의료_prefecture.csv",
    "cleaned_estat_J": "estat_J_복지_prefecture.csv",
    "cleaned_kosis_aging": "kosis_고령인구비율.csv",
    "cleaned_kosis_beds": "kosis_의료기관병상수.csv",
    "cleaned_kosis_care": "kosis_장기요양기관현황.csv",
    "cleaned_kosis_regpop": "kosis_주민등록인구현황.csv",
}

CREATE_RAW_TABLES_SQL = "00_create_raw_tables.sql"

# 1단계: 원본 -> 소스별 1:1 정제 (data/cleaned/*.csv에 대응)
SOURCE_CLEANING_SQL_FILES = [
    "01_clean_estat_A.sql",
    "02_clean_estat_I.sql",
    "03_clean_estat_J.sql",
    "04_clean_kosis_aging.sql",
    "05_clean_kosis_beds.sql",
    "06_clean_kosis_care.sql",
    "07_clean_kosis_regpop.sql",
]

# 2단계: 정제된 소스 -> ERD 최종 테이블(Dim_Country/Dim_Region/Dim_Date/Fact_RegionStats/뷰)
ERD_BUILD_SQL_FILES = [
    "08_merge_korea.sql",
    "09_merge_japan.sql",
    "10_combine_and_filter_years.sql",
    "11_add_derived_columns.sql",
    "12_add_pop_change_rate.sql",
    "13_build_dim_country.sql",
    "14_build_dim_region.sql",
    "15_build_dim_date.sql",
    "16_build_fact_regionstats.sql",
    "17_build_views.sql",
]


def load_raw_csv_to_sqlite(conn: sqlite3.Connection):
    """원본 CSV 7개를 raw_* 테이블에 '있는 그대로' 넣는다 (필터링/변환 없음)."""
    for table, filename in RAW_SOURCES.items():
        df = pd.read_csv(os.path.join(RAW_DIR, filename), dtype=str, encoding="utf-8-sig")
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  {table} <- {filename} ({len(df)}행 그대로 적재)")


def run_sql_file(conn: sqlite3.Connection, filename: str):
    """.sql 파일을 문장 단위로 실행하고, SELECT 문의 결과는 그 자리에서 출력한다
    (진짜 SQL 클라이언트에서 한 줄씩 실행하며 결과를 확인하는 것과 같은 방식)."""
    path = os.path.join(SQL_DIR, filename)
    with open(path, encoding="utf-8") as f:
        script = f.read()
    statements = [s.strip() for s in script.split(";") if s.strip()]
    print(f"  실행: {filename}")
    for stmt in statements:
        cur = conn.execute(stmt)
        if cur.description is not None:  # SELECT처럼 결과 행을 반환하는 문장인지 확인
            for row in cur.fetchall():
                print(f"    -> {row}")
    conn.commit()


def verify_cleaned_sources(conn: sqlite3.Connection):
    print("\n=== 검증 1: cleaned_* 테이블 행수 vs data/cleaned/*.csv 행수 ===")
    all_match = True
    for table, filename in CLEANED_CHECKS.items():
        n_sql = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        n_csv = len(pd.read_csv(os.path.join(CLEANED_DIR, filename)))
        mark = "OK" if n_sql == n_csv else "!! 불일치"
        all_match &= n_sql == n_csv
        print(f"  {table}: SQL {n_sql}행 / CSV {n_csv}행  [{mark}]")
    print("전체 일치" if all_match else "일부 불일치 있음 - SQL 로직 재확인 필요")


def verify_against_production_db(conn: sqlite3.Connection):
    """cleaning_process.db에서 SQL만으로 조립한 Fact_RegionStats가
    실제 운영 DB(aging_infra.db, pandas로 만든 것)와 값까지 완전히 같은지 대조한다.
    region_id 번호 자체가 우연히 같은지는 중요하지 않으므로, country/지역명/연도
    같은 '사람이 읽을 수 있는 키'로 맞춰서 비교한다."""
    if not os.path.exists(PROD_DB_PATH):
        print("\n(운영 DB aging_infra.db가 없어 대조를 건너뜀)")
        return

    conn.execute(f"ATTACH DATABASE '{PROD_DB_PATH}' AS prod")

    def readable(prefix: str) -> str:
        return f"""
            SELECT r.country, r.region_name_kr, d.year,
                   f.total_pop, f.elderly_pop, f.medical_beds, f.care_facility_count,
                   ROUND(f.aging_rate, 6) AS aging_rate,
                   ROUND(f.pop_change_rate, 6) AS pop_change_rate,
                   ROUND(f.medical_beds_per_10k, 6) AS medical_beds_per_10k,
                   ROUND(f.care_facility_per_10k, 6) AS care_facility_per_10k
            FROM {prefix}Fact_RegionStats f
            JOIN {prefix}Dim_Region r ON r.region_id = f.region_id
            JOIN {prefix}Dim_Date d ON d.date_id = f.date_id
        """

    n_sql_only = conn.execute(
        f"SELECT COUNT(*) FROM ({readable('main.')} EXCEPT {readable('prod.')})"
    ).fetchone()[0]
    n_prod_only = conn.execute(
        f"SELECT COUNT(*) FROM ({readable('prod.')} EXCEPT {readable('main.')})"
    ).fetchone()[0]

    print("\n=== 검증 2: SQL로 조립한 Fact_RegionStats vs 운영 DB(aging_infra.db) 값 대조 ===")
    print(f"  cleaning_process.db에만 있는(=값이 다른) 행: {n_sql_only}")
    print(f"  aging_infra.db에만 있는(=값이 다른) 행: {n_prod_only}")
    if n_sql_only == 0 and n_prod_only == 0:
        print("  576행 전부 country/지역명/연도/모든 지표 값까지 완전히 일치")
    else:
        print("  !! 불일치 있음 - SQL 로직과 preprocess_and_load.py 로직 차이 재확인 필요")

    conn.execute("DETACH DATABASE prod")


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)

    print("1) raw_* 테이블 스키마 생성")
    run_sql_file(conn, CREATE_RAW_TABLES_SQL)

    print("\n2) 원본 CSV -> raw_* 테이블 적재")
    load_raw_csv_to_sqlite(conn)

    print("\n3) SQL 정제 스크립트 실행 (원본 -> 소스별 1:1 정제)")
    for filename in SOURCE_CLEANING_SQL_FILES:
        run_sql_file(conn, filename)

    print("\n4) SQL로 ERD 최종 테이블 조립 (정제 소스 -> Dim/Fact)")
    for filename in ERD_BUILD_SQL_FILES:
        run_sql_file(conn, filename)

    verify_cleaned_sources(conn)
    verify_against_production_db(conn)

    conn.close()
    print(f"\n완료: {DB_PATH}")
