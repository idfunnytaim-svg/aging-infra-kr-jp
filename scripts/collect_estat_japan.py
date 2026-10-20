"""
e-Stat API로 일본 도도부현별 고령화·의료·복지 데이터 자동 수집
================================================================

이전 버전 대비 수정 사항 (2026-08-24):
- [버그] e-Stat API는 한 번 요청에 최대 10만 건까지만 반환한다. 이 통계표는
  실제로는 시구정촌(市区町村) x 항목 x 연도 조합이 100만 건을 넘어가는데
  이전 스크립트는 첫 10만 건만 받고 끝나서, 정작 필요한 항목
  (65세이상인구=A1303, 병상수=I5211/I5212 등)이 아예 잘려서 누락되었다.
  -> cdCat01로 필요한 항목만 지정해서 요청량 자체를 줄이고,
     startPosition/NEXT_KEY 기반 페이지네이션으로 남은 데이터를 모두 받는다.
- [단위] 이 통계표(0000020201 등)에는애초에 도도부현(레벨1) 행이 없고
  시구정촌(레벨2) / 구(레벨3)만 있다. 레벨3(구)은 상위 레벨2(시) 값에
  이미 포함되므로 레벨2만 골라서 지역명 앞부분(도도부현명)으로 묶어
  도도부현 단위로 합산한다.
- [보안] API 키를 코드에서 제거하고 .env 파일에서 읽어온다.

수정 사항 (2026-08-24 (3)):
- [데이터 소스 교체] 인구(A_인구세대)를 국세조사 원자료(0000020201, 5년마다인
  2015·2020년만 존재)에서 e-Stat의 **인구추계(人口推計)** 통계표로 교체.
  인구추계는 국세조사를 벤치마크로 출생·사망·이동 통계를 결합해 매년 10월 1일
  기준으로 총무성 통계국이 공식 발표하는 추계치이며, 이미 도도부현 단위로 제공되어
  시구정촌 합산 로직이 필요 없다. 두 census 기준연도 시리즈를 이어붙이면 빈틈 없이
  2015~2024년 매년 데이터를 얻을 수 있다:
    - 平成27年(2015)국세조사 기준 統計表010 (statsDataId=0003459027): 2015~2019
    - 令和2年(2020)국세조사 기준 統計表010 (statsDataId=0003448237): 2020~2024
  총인구(cat03=001, 일본인만 집계한 002는 제외)와 65세이상인구(5세계급 65~69 ~
  85세이상 5개 구간 합산)만 추출한다. 자세한 검토 내용은
  docs/원본데이터_점검.md 2.1 참고.

사전 준비:
1. https://www.e-stat.go.jp 회원가입 (이메일 인증만 필요, 본인인증 불필요)
2. 마이페이지 > API機能 에서 appId 발급
3. 프로젝트 루트(고령화/)에 .env 파일을 만들고 아래처럼 채워넣기:
       ESTAT_APP_ID=발급받은_appId

설치:
    pip install requests pandas --break-system-packages
"""

import os
import time
import requests
import pandas as pd

# ============================================================
# .env 로드 (별도 패키지 없이 간단히 직접 파싱)
# ============================================================

def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))

ESTAT_APP_ID = os.environ.get("ESTAT_APP_ID")
if not ESTAT_APP_ID:
    raise RuntimeError(
        "ESTAT_APP_ID가 설정되지 않았습니다. 고령화/.env 파일에 "
        "ESTAT_APP_ID=발급받은_appId 를 추가하세요."
    )

API_VERSION = "2.1"
MAX_RECORDS_PER_REQUEST = 100000  # e-Stat API 응답 상한

# ============================================================
# CONFIG: 분야별 statsDataId + 실제 필요한 항목(cat01) 코드
# ============================================================
# 아래 cat01 코드는 e-Stat 메타데이터(metaGetFlg=Y)를 직접 조회해서 확인한 값.
# 항목명은 GET_STATS_DATA > CLASS_INF > CLASS_OBJ(id=cat01) 에서 확인 가능.

# 인구(A_인구세대)는 국세조사 원자료 대신 인구추계 統計表010을 별도 함수
# (fetch_population_estimates)로 수집한다 — 아래 TABLES에는 포함하지 않음.
POP_ESTIMATE_SERIES = [
    ("0003459027", "2015년국세조사기준"),  # 2015~2019
    ("0003448237", "2020년국세조사기준"),  # 2020~2024
]
# cat02(연령5세계급) 코드: 01000=총수, 65세이상 5개 구간(65~69 ~ 80~84, 85세이상)
POP_CAT02_TOTAL = "01000"
POP_CAT02_65PLUS = ["01014", "01015", "01016", "01017", "04018"]

TABLES = {
    "I_의료": {
        "stats_data_id": "0000020209",
        "cat01": ["I5211", "I5212"],  # 병원 병상수, 일반진료소 병상수
    },
    "J_복지": {
        "stats_data_id": "0000020210",
        # 개호노인복지시설 수/정원(장기요양 인프라 대용). 조사양식이 2018년 전후로
        # 詳細票(J230121/J230124) -> 基本票(J230127/J230128)로 바뀌면서 코드가
        # 나뉘어 있음. 둘 다 받아서 연속된 시계열로 합친다.
        "cat01": ["J230121", "J230124", "J230127", "J230128"],
    },
}

# 詳細票/基本票 등 조사양식 차이로 갈라진 항목명을 하나의 지표로 합치기 위한 매핑
CAT01_NAME_UNIFY = {
    "J230121_介護老人福祉施設数（詳細票）": "介護老人福祉施設数",
    "J230127_介護老人福祉施設数（基本票）": "介護老人福祉施設数",
    "J230124_介護老人福祉施設定員数（詳細票）": "介護老人福祉施設定員数",
    "J230128_介護老人福祉施設定員数（基本票）": "介護老人福祉施設定員数",
}

# 분석 대상 연도 범위 (KOSIS 쪽 수집 범위와 통일)
TIME_FROM = "2015100000"
TIME_TO = "2024100000"


# ============================================================
# 수집 함수
# ============================================================

def fetch_estat_page(stats_data_id: str, cat01_codes: list, start_position: int):
    url = f"https://api.e-stat.go.jp/rest/{API_VERSION}/app/json/getStatsData"
    params = {
        "appId": ESTAT_APP_ID,
        "lang": "J",
        "statsDataId": stats_data_id,
        "cdCat01": ",".join(cat01_codes),
        "cdTimeFrom": TIME_FROM,
        "cdTimeTo": TIME_TO,
        "metaGetFlg": "Y",
        "cntGetFlg": "N",
        "sectionHeaderFlg": "1",
        "startPosition": start_position,
    }
    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()

    result = data.get("GET_STATS_DATA", {}).get("RESULT", {})
    if result.get("STATUS") != 0:
        raise RuntimeError(f"e-Stat API 오류: {result.get('ERROR_MSG')}")

    return data["GET_STATS_DATA"]["STATISTICAL_DATA"]


def fetch_estat(stats_data_id: str, cat01_codes: list) -> pd.DataFrame:
    """cat01/연도로 좁힌 뒤에도 10만 건이 넘을 수 있으므로 끝까지 페이지네이션."""
    all_values = []
    code_maps = {}
    area_levels = {}
    start_position = 1

    while True:
        stat_data = fetch_estat_page(stats_data_id, cat01_codes, start_position)
        values = stat_data["DATA_INF"]["VALUE"]
        if isinstance(values, dict):
            values = [values]
        all_values.extend(values)

        # 메타정보는 첫 페이지에서만 파싱하면 충분 (매 페이지 동일)
        if not code_maps:
            class_objs = stat_data.get("CLASS_INF", {}).get("CLASS_OBJ", [])
            for obj in class_objs:
                obj_id = obj.get("@id")
                classes = obj.get("CLASS")
                if isinstance(classes, dict):
                    classes = [classes]
                if classes:
                    code_maps[obj_id] = {c["@code"]: c["@name"] for c in classes}
                    if obj_id == "area":
                        area_levels = {c["@code"]: c.get("@level") for c in classes}

        result_inf = stat_data.get("RESULT_INF", {})
        total = result_inf.get("TOTAL_NUMBER", len(all_values))
        to_number = result_inf.get("TO_NUMBER", len(all_values))
        next_key = result_inf.get("NEXT_KEY")
        print(f"    {to_number}/{total} 건 수신...")

        if not next_key or int(to_number) >= int(total):
            break
        start_position = int(next_key)
        time.sleep(0.5)

    df = pd.DataFrame(all_values)
    return df, code_maps, area_levels


def apply_code_maps(df: pd.DataFrame, code_maps: dict) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        key = col.lstrip("@")
        if key in code_maps:
            df[f"{key}_name"] = df[col].map(code_maps[key])
    return df


def aggregate_to_prefecture(df: pd.DataFrame, area_levels: dict) -> pd.DataFrame:
    """레벨2(시구정촌) 행만 남기고, 지역명 앞부분(도도부현명)으로 묶어 합산.
    레벨3(구)는 상위 레벨2 시 값에 이미 포함되어 있으므로 제외해야 이중 집계를 피한다."""
    df = df.copy()
    df["area_level"] = df["@area"].map(area_levels)
    muni = df[df["area_level"] == "2"].copy()

    muni["prefecture"] = muni["area_name"].str.split(" ", n=1).str[0]
    muni["value"] = pd.to_numeric(muni["$"], errors="coerce")
    muni["cat01_name"] = muni["cat01_name"].replace(CAT01_NAME_UNIFY)

    agg = (
        muni.groupby(["prefecture", "cat01_name", "time_name"], as_index=False)["value"]
        .sum()
    )
    return agg


def fetch_population_estimates() -> pd.DataFrame:
    """인구추계 統計表010(2015~2019, 2020~2024 두 시리즈)을 이어붙여
    도도부현별 총인구·65세이상인구를 매년(2015~2024) 산출한다."""
    all_rows = []

    for stats_data_id, series_label in POP_ESTIMATE_SERIES:
        print(f"[e-Stat] 수집 중: 인구추계 {series_label} ({stats_data_id})")
        url = f"https://api.e-stat.go.jp/rest/{API_VERSION}/app/json/getStatsData"
        params = {
            "appId": ESTAT_APP_ID,
            "lang": "J",
            "statsDataId": stats_data_id,
            "cdCat01": "000",  # 男女計
            "cdCat02": ",".join([POP_CAT02_TOTAL] + POP_CAT02_65PLUS),
            "cdCat03": "001",  # 総人口 (日本人人口=002は除外)
            "metaGetFlg": "Y",
            "cntGetFlg": "N",
        }
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        result = data.get("GET_STATS_DATA", {}).get("RESULT", {})
        if result.get("STATUS") != 0:
            raise RuntimeError(f"e-Stat API 오류: {result.get('ERROR_MSG')}")

        stat_data = data["GET_STATS_DATA"]["STATISTICAL_DATA"]
        values = stat_data["DATA_INF"]["VALUE"]
        if isinstance(values, dict):
            values = [values]

        class_objs = stat_data.get("CLASS_INF", {}).get("CLASS_OBJ", [])
        code_maps = {}
        for obj in class_objs:
            obj_id = obj.get("@id")
            classes = obj.get("CLASS")
            if isinstance(classes, dict):
                classes = [classes]
            if classes:
                code_maps[obj_id] = {c["@code"]: c["@name"] for c in classes}

        df = pd.DataFrame(values)
        df["area_name"] = df["@area"].map(code_maps["area"])
        df["cat02_name"] = df["@cat02"].map(code_maps["cat02"])
        df["time_name"] = df["@time"].map(code_maps["time"])
        # 이 통계표의 단위는 "千人"(천명)이다. 국세조사 원자료(구 A1101/A1303)는
        # 실인원수였고, 다른 e-Stat 표(병상수·요양시설수)도 실수 단위이므로
        # 1000을 곱해 실인원수로 맞춘다.
        df["value"] = pd.to_numeric(df["$"], errors="coerce") * 1000

        df = df[df["@area"] != "00000"].copy()  # 全国 합계 제외, 47도도부현만
        df["year"] = df["time_name"].str.extract(r"(\d{4})")[0]

        total = df[df["@cat02"] == POP_CAT02_TOTAL].copy()
        total["cat01_name"] = "A1101_総人口"

        plus65 = (
            df[df["@cat02"].isin(POP_CAT02_65PLUS)]
            .groupby(["area_name", "year"], as_index=False)["value"]
            .sum()
        )
        plus65["cat01_name"] = "A1303_65歳以上人口"

        for part in (total[["area_name", "year", "value", "cat01_name"]], plus65):
            part = part.rename(columns={"area_name": "prefecture", "year": "time_name"})
            part["time_name"] = part["time_name"] + "年度"
            all_rows.append(part[["prefecture", "cat01_name", "time_name", "value"]])

    return pd.concat(all_rows, ignore_index=True).sort_values(
        ["prefecture", "cat01_name", "time_name"]
    )


def collect_all() -> dict:
    results = {"A_인구세대": fetch_population_estimates()}
    for name, cfg in TABLES.items():
        print(f"[e-Stat] 수집 중: {name} ({cfg['stats_data_id']}, cat01={cfg['cat01']})")
        try:
            df, code_maps, area_levels = fetch_estat(cfg["stats_data_id"], cfg["cat01"])
            df = apply_code_maps(df, code_maps)
            pref_df = aggregate_to_prefecture(df, area_levels)
            results[name] = pref_df
        except Exception as e:
            print(f"  -> 실패: {e}")
    return results


# ============================================================
# 실행부
# ============================================================

if __name__ == "__main__":
    print("=== e-Stat 데이터 수집 시작 (도도부현 단위 집계) ===")
    data = collect_all()
    for name, df in data.items():
        out_path = f"../data/raw/estat_{name}_prefecture.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {out_path} ({len(df)} rows, {df['prefecture'].nunique()}개 도도부현)")
        print(df.head())
