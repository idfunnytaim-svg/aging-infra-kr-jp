"""ERD/전처리 검증용: data/raw/의 원본 CSV 7개를 1:1로 정제해서
data/cleaned/에 저장한다. preprocess_and_load.py가 최종 DB로 합치기 전
단계에서, "원본 파일 → 정제 파일"이 어떻게 필터링/변환되는지 소스 단위로
그대로 보여주는 것이 목적 — Fact_RegionStats처럼 병합/파생하지 않는다.

각 파일의 정제 규칙은 docs/전처리_로그.md, docs/원본데이터_점검.md 2장과 동일.
"""
import os

import pandas as pd

from preprocess_and_load import JP_PREF_KR, KR_REGIONS_17, RAW_DIR

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")


def clean_estat_A():
    df = pd.read_csv(os.path.join(RAW_DIR, "estat_A_인구세대_prefecture.csv"))
    df["year"] = df["time_name"].str.replace("年度", "", regex=False).astype(int)
    df = df.pivot_table(index=["prefecture", "year"], columns="cat01_name", values="value", aggfunc="first").reset_index()
    df = df.rename(columns={"A1101_総人口": "total_pop", "A1303_65歳以上人口": "elderly_pop"})
    df.insert(0, "region_name_kr", df["prefecture"].map(JP_PREF_KR))
    df = df.rename(columns={"prefecture": "region_name_local"})
    return df[["region_name_kr", "region_name_local", "year", "total_pop", "elderly_pop"]].sort_values(
        ["region_name_kr", "year"])


def clean_estat_I():
    df = pd.read_csv(os.path.join(RAW_DIR, "estat_I_의료_prefecture.csv"))
    df["year"] = df["time_name"].str.replace("年度", "", regex=False).astype(int)
    # I5211(병원 병상수) + I5212(일반진료소 병상수) 합산 — docs/데이터출처.md 2번 항목과 동일
    df = df.groupby(["prefecture", "year"], as_index=False)["value"].sum()
    df = df.rename(columns={"value": "medical_beds"})
    df.insert(0, "region_name_kr", df["prefecture"].map(JP_PREF_KR))
    df = df.rename(columns={"prefecture": "region_name_local"})
    return df[["region_name_kr", "region_name_local", "year", "medical_beds"]].sort_values(
        ["region_name_kr", "year"])


def clean_estat_J():
    df = pd.read_csv(os.path.join(RAW_DIR, "estat_J_복지_prefecture.csv"))
    df["year"] = df["time_name"].str.replace("年度", "", regex=False).astype(int)
    # 개호노인복지시설 "정원수"는 버리고 "시설수"만 사용
    df = df[df["cat01_name"] == "介護老人福祉施設数"]
    df = df.rename(columns={"value": "care_facility_count"})
    df.insert(0, "region_name_kr", df["prefecture"].map(JP_PREF_KR))
    df = df.rename(columns={"prefecture": "region_name_local"})
    return df[["region_name_kr", "region_name_local", "year", "care_facility_count"]].sort_values(
        ["region_name_kr", "year"])


def clean_kosis_aging():
    df = pd.read_csv(os.path.join(RAW_DIR, "kosis_고령인구비율.csv"))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["region"].isin(KR_REGIONS_17)]
    df = df.pivot_table(index=["region", "year"], columns="item", values="value", aggfunc="first").reset_index()
    df = df.rename(columns={
        "region": "region_name_kr",
        "65세이상인구(A)": "elderly_pop",
        "전체인구(B)": "total_pop",
        "고령인구비율(A÷B×100)": "aging_rate_source",
    })
    return df[["region_name_kr", "year", "total_pop", "elderly_pop", "aging_rate_source"]].sort_values(
        ["region_name_kr", "year"])


def clean_kosis_beds():
    df = pd.read_csv(os.path.join(RAW_DIR, "kosis_의료기관병상수.csv"))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["region"].isin(KR_REGIONS_17) & (df["item"] == "총병상수(A)")]
    df = df.rename(columns={"region": "region_name_kr", "value": "medical_beds"})
    return df[["region_name_kr", "year", "medical_beds"]].sort_values(["region_name_kr", "year"])


def clean_kosis_care():
    df = pd.read_csv(os.path.join(RAW_DIR, "kosis_장기요양기관현황.csv"))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    # category2(시설유형 세부축)가 "계"(합계)인 행만 — 세부유형별 중복 방지
    df = df[(df["region"] != "합계") & (df["item"] == "기관수") & (df["category2"] == "계")]
    df = df.rename(columns={"region": "region_name_kr", "value": "care_facility_count"})
    return df[["region_name_kr", "year", "care_facility_count"]].sort_values(["region_name_kr", "year"])


def clean_kosis_reg_pop():
    # 미사용(중복) 파일이지만 요청대로 동일 규칙으로 정제해 보존
    df = pd.read_csv(os.path.join(RAW_DIR, "kosis_주민등록인구현황.csv"))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["region"].isin(KR_REGIONS_17) & (df["item"] == "총인구수")]
    df = df.rename(columns={"region": "region_name_kr", "value": "total_pop"})
    return df[["region_name_kr", "year", "total_pop"]].sort_values(["region_name_kr", "year"])


CLEANERS = [
    ("estat_A_인구세대_prefecture.csv", clean_estat_A),
    ("estat_I_의료_prefecture.csv", clean_estat_I),
    ("estat_J_복지_prefecture.csv", clean_estat_J),
    ("kosis_고령인구비율.csv", clean_kosis_aging),
    ("kosis_의료기관병상수.csv", clean_kosis_beds),
    ("kosis_장기요양기관현황.csv", clean_kosis_care),
    ("kosis_주민등록인구현황.csv", clean_kosis_reg_pop),
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for filename, cleaner in CLEANERS:
        df = cleaner()
        out_path = os.path.join(OUT_DIR, filename)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"{filename}: {len(df)}행 -> {out_path}")


if __name__ == "__main__":
    main()
