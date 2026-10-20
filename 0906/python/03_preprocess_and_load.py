# ============================================================
# [0906 설명용 사본] 원본: scripts/preprocess_and_load.py
# 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
# 실제 운영 코드는 원본 경로에 있으며, 이 파일은 로직을 바꾸지 않은 복사본입니다.
# ============================================================

"""
원본 CSV(data/raw/) 전처리 후 SQLite(data/aging_infra.db)에 적재
================================================================

전제: docs/원본데이터_점검.md에서 정리한 결정 사항을 그대로 따른다.
- 한국 KOSIS 3개 파일(고령인구비율/장기요양기관현황/의료기관병상수)은 시도+시군구가
  섞여 있으므로 정확히 17개 시도명과 일치하는 행만 남긴다.
- `kosis_주민등록인구현황.csv`는 총인구 항목이 고령인구비율과 중복이라 사용하지 않는다.
- 일본 인구는 census(0000020201) 대신 인구추계(統計表010) 기반으로 이미 2015~2024
  매년 수집돼 있다 (`collect_estat_japan.py` 2026-08-24 (3) 참고).
- 코로나(2020~2022) 기간은 별도 변수로 구분하지 않고 전체 시계열을 그대로 쓴다.
- 2026-08-26(5): 팀/보고서 요청으로 적재 연도를 2015~2023으로 통일한다. 일본 병상수·
  요양기관수 원자료가 2023년까지만 있어(`docs/원본데이터_점검.md` 1장) 2024년에는
  일본만 인프라 지표가 빈 값이었는데, 인구 지표까지 포함해 전체를 2023년까지로 잘라
  모든 컬럼에 결측치가 없는 데이터셋으로 통일했다. 원본 CSV(data/raw/)에는 2024년치도
  그대로 남아있고, 이 스크립트가 로드할 때만 YEARS 범위로 걸러낸다.

실행:
    python3 preprocess_and_load.py
"""

import os
import sqlite3

import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "aging_infra.db")
DDL_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "ddl", "create_tables.sql")

YEARS = list(range(2015, 2024))  # 2015~2023 (양국 모두 결측 없는 공통 구간으로 통일)

KR_REGIONS_17 = [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시",
    "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도", "전북특별자치도",
    "전라남도", "경상북도", "경상남도", "제주특별자치도",
]

# 일본 47도도부현 한자 -> 한글 표기 매핑 (Dim_Region.region_name_kr용)
JP_PREF_KR = {
    "北海道": "홋카이도", "青森県": "아오모리현", "岩手県": "이와테현", "宮城県": "미야기현",
    "秋田県": "아키타현", "山形県": "야마가타현", "福島県": "후쿠시마현", "茨城県": "이바라키현",
    "栃木県": "도치기현", "群馬県": "군마현", "埼玉県": "사이타마현", "千葉県": "지바현",
    "東京都": "도쿄도", "神奈川県": "가나가와현", "新潟県": "니가타현", "富山県": "도야마현",
    "石川県": "이시카와현", "福井県": "후쿠이현", "山梨県": "야마나시현", "長野県": "나가노현",
    "岐阜県": "기후현", "静岡県": "시즈오카현", "愛知県": "아이치현", "三重県": "미에현",
    "滋賀県": "시가현", "京都府": "교토부", "大阪府": "오사카부", "兵庫県": "효고현",
    "奈良県": "나라현", "和歌山県": "와카야마현", "鳥取県": "돗토리현", "島根県": "시마네현",
    "岡山県": "오카야마현", "広島県": "히로시마현", "山口県": "야마구치현", "徳島県": "도쿠시마현",
    "香川県": "가가와현", "愛媛県": "에히메현", "高知県": "고치현", "福岡県": "후쿠오카현",
    "佐賀県": "사가현", "長崎県": "나가사키현", "熊本県": "구마모토현", "大分県": "오이타현",
    "宮崎県": "미야자키현", "鹿児島県": "가고시마현", "沖縄県": "오키나와현",
}


# ============================================================
# 한국 데이터 전처리
# ============================================================

def load_korea() -> pd.DataFrame:
    pop = pd.read_csv(os.path.join(RAW_DIR, "kosis_고령인구비율.csv"))
    pop["value"] = pd.to_numeric(pop["value"], errors="coerce")
    pop = pop[pop["region"].isin(KR_REGIONS_17)]
    pop = pop.pivot_table(index=["region", "year"], columns="item", values="value", aggfunc="first").reset_index()
    pop = pop.rename(columns={
        "65세이상인구(A)": "elderly_pop",
        "전체인구(B)": "total_pop",
        "고령인구비율(A÷B×100)": "aging_rate",
    })

    beds = pd.read_csv(os.path.join(RAW_DIR, "kosis_의료기관병상수.csv"))
    beds["value"] = pd.to_numeric(beds["value"], errors="coerce")
    beds = beds[beds["region"].isin(KR_REGIONS_17) & (beds["item"] == "총병상수(A)")]
    beds = beds[["region", "year", "value"]].rename(columns={"value": "medical_beds"})

    care = pd.read_csv(os.path.join(RAW_DIR, "kosis_장기요양기관현황.csv"))
    care["value"] = pd.to_numeric(care["value"], errors="coerce")
    # category2(시설유형 세부축)가 "계"(합계)인 행만 남긴다 — 안 그러면 방문요양/노인요양시설
    # 등 세부유형별 행까지 같은 item명("기관수")으로 남아 region+year당 중복이 생긴다.
    care = care[(care["region"] != "합계") & (care["item"] == "기관수") & (care["category2"] == "계")]
    care = care[["region", "year", "value"]].rename(columns={"value": "care_facility_count"})

    df = pop.merge(beds, on=["region", "year"], how="left").merge(care, on=["region", "year"], how="left")
    df["year"] = df["year"].astype(int)
    df["region_name_kr"] = df["region"]
    df["country"] = "KR"
    df["region_name_local"] = None
    return df[["country", "region_name_kr", "region_name_local", "year",
               "total_pop", "elderly_pop", "aging_rate", "medical_beds", "care_facility_count"]]


# ============================================================
# 일본 데이터 전처리
# ============================================================

def load_japan() -> pd.DataFrame:
    def year_of(time_name: str) -> int:
        return int(time_name.replace("年度", ""))

    pop = pd.read_csv(os.path.join(RAW_DIR, "estat_A_인구세대_prefecture.csv"))
    pop["year"] = pop["time_name"].map(year_of)
    pop = pop.pivot_table(index=["prefecture", "year"], columns="cat01_name", values="value", aggfunc="first").reset_index()
    pop = pop.rename(columns={"A1101_総人口": "total_pop", "A1303_65歳以上人口": "elderly_pop"})

    beds = pd.read_csv(os.path.join(RAW_DIR, "estat_I_의료_prefecture.csv"))
    beds["year"] = beds["time_name"].map(year_of)
    beds = beds.groupby(["prefecture", "year"], as_index=False)["value"].sum()
    beds = beds.rename(columns={"value": "medical_beds"})

    care = pd.read_csv(os.path.join(RAW_DIR, "estat_J_복지_prefecture.csv"))
    care["year"] = care["time_name"].map(year_of)
    care = care[care["cat01_name"] == "介護老人福祉施設数"]
    care = care[["prefecture", "year", "value"]].rename(columns={"value": "care_facility_count"})

    df = pop.merge(beds, on=["prefecture", "year"], how="left").merge(care, on=["prefecture", "year"], how="left")
    df["aging_rate"] = df["elderly_pop"] / df["total_pop"] * 100
    df["region_name_kr"] = df["prefecture"].map(JP_PREF_KR)
    df["region_name_local"] = df["prefecture"]
    df["country"] = "JP"
    return df[["country", "region_name_kr", "region_name_local", "year",
               "total_pop", "elderly_pop", "aging_rate", "medical_beds", "care_facility_count"]]


# ============================================================
# 이상치 확인 (기획서 2.3 "이상치" 항목 — 원자료와 대조하여 확인)
# ============================================================

def check_outliers(df: pd.DataFrame) -> None:
    checks = [
        ("total_pop", df["total_pop"] <= 0, "총인구가 0 이하"),
        ("elderly_pop", df["elderly_pop"] <= 0, "65세이상인구가 0 이하"),
        ("elderly_pop > total_pop", df["elderly_pop"] > df["total_pop"], "65세이상인구가 총인구보다 큼"),
        ("aging_rate", (df["aging_rate"] < 0) | (df["aging_rate"] > 100), "고령화율이 0~100% 범위 밖"),
        ("medical_beds", df["medical_beds"] < 0, "병상수가 음수"),
        ("care_facility_count", df["care_facility_count"] < 0, "장기요양기관수가 음수"),
    ]
    print("\n=== 이상치 확인 ===")
    for name, mask, desc in checks:
        n = int(mask.sum())
        if n:
            rows = df.loc[mask, ["country", "region_name_kr", "year"]].to_dict("records")
            print(f"  ⚠ {name}: {desc} — {n}건")
            for r in rows[:5]:
                print(f"      {r}")
        else:
            print(f"  ✓ {name}: {desc} — 이상 없음")


# ============================================================
# 파생변수 + Dim/Fact 테이블 구성
# ============================================================

def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["country", "region_name_kr", "year"]).copy()
    prev_pop = df.groupby(["country", "region_name_kr"])["total_pop"].shift(1)
    df["pop_change_rate"] = (df["total_pop"] - prev_pop) / prev_pop * 100
    df["medical_beds_per_10k"] = df["medical_beds"] / (df["total_pop"] / 10_000)
    df["care_facility_per_10k"] = df["care_facility_count"] / (df["total_pop"] / 10_000)
    return df


def build_dim_region(df: pd.DataFrame) -> pd.DataFrame:
    regions = (
        df[["country", "region_name_kr", "region_name_local"]]
        .drop_duplicates()
        .sort_values(["country", "region_name_kr"])
        .reset_index(drop=True)
    )
    regions.insert(0, "region_id", regions.index + 1)
    return regions


def build_dim_date() -> pd.DataFrame:
    return pd.DataFrame({"date_id": [y - YEARS[0] + 1 for y in YEARS], "year": YEARS})


def build_fact(df: pd.DataFrame, dim_region: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    fact = df.merge(dim_region, on=["country", "region_name_kr", "region_name_local"], how="left")
    fact = fact.merge(dim_date, on="year", how="left")
    return fact[["region_id", "date_id",
                 "total_pop", "elderly_pop", "medical_beds", "care_facility_count",
                 "aging_rate", "pop_change_rate",
                 "medical_beds_per_10k", "care_facility_per_10k"]]


# ============================================================
# SQLite 적재
# ============================================================

def load_to_sqlite(dim_region: pd.DataFrame, dim_date: pd.DataFrame, fact: pd.DataFrame):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(DDL_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    dim_region.to_sql("Dim_Region", conn, if_exists="append", index=False)
    dim_date.to_sql("Dim_Date", conn, if_exists="append", index=False)
    fact.to_sql("Fact_RegionStats", conn, if_exists="append", index=False)
    conn.commit()

    print("\n=== 적재 결과 검증 ===")
    for tbl in ["Dim_Country", "Dim_Region", "Dim_Date", "Fact_RegionStats",
                "Fact_Population", "Fact_Infra"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"{tbl}: {n}행")

    print("\n국가별 지역 수:")
    for row in conn.execute("SELECT country, COUNT(*) FROM Dim_Region GROUP BY country"):
        print(" ", row)

    print("\n결측(NULL) 현황 (Fact_RegionStats):")
    for col in ["total_pop", "elderly_pop", "medical_beds", "care_facility_count",
                "aging_rate", "pop_change_rate", "medical_beds_per_10k", "care_facility_per_10k"]:
        n_null = conn.execute(f"SELECT COUNT(*) FROM Fact_RegionStats WHERE {col} IS NULL").fetchone()[0]
        print(f"  {col}: {n_null}개 NULL")

    conn.close()


if __name__ == "__main__":
    print("한국 데이터 전처리 중...")
    kr = load_korea()
    print(f"  {kr.shape[0]}행, 지역 {kr['region_name_kr'].nunique()}개, 연도 {sorted(kr['year'].unique())}")

    print("일본 데이터 전처리 중...")
    jp = load_japan()
    print(f"  {jp.shape[0]}행, 지역 {jp['region_name_kr'].nunique()}개, 연도 {sorted(jp['year'].unique())}")

    combined = pd.concat([kr, jp], ignore_index=True)
    combined = combined[combined["year"].isin(YEARS)].reset_index(drop=True)
    check_outliers(combined)
    combined = add_derived_columns(combined)

    dim_region = build_dim_region(combined)
    dim_date = build_dim_date()
    fact = build_fact(combined, dim_region, dim_date)

    print(f"\nDim_Region {len(dim_region)}행, Dim_Date {len(dim_date)}행, Fact_RegionStats {len(fact)}행")
    load_to_sqlite(dim_region, dim_date, fact)
    print(f"\nSQLite DB 저장 완료: {DB_PATH}")
