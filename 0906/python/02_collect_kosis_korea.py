# ============================================================
# [0906 설명용 사본] 원본: scripts/collect_kosis_korea.py
# 이 폴더의 역할과 전체 그림은 00_설명.md 참고.
# 실제 운영 코드는 원본 경로에 있으며, 이 파일은 로직을 바꾸지 않은 복사본입니다.
# ============================================================

"""
KOSIS Open API로 한국 시도별 고령화·인구·인프라 데이터 자동 수집
================================================================

사전 준비:
1. https://kosis.kr 회원가입 (본인인증 필요 - 한국에서 진행)
2. 로그인 후 Open API > 활용신청 > 인증키 발급 (자동승인, 즉시 발급)

설치:
    pip install requests pandas --break-system-packages

수정 이력:
- res.encoding = "utf-8" 추가 (JSON 파싱이 느려지는 문제 해결)
- item 컬럼의 <br> 태그 제거
- 통계표별로 지역 파라미터명이 다른 경우(objL1 / objL) 대응
- [보안] API 키를 코드에서 제거하고 .env 파일에서 읽어오도록 변경 (2026-08-24)

사전 준비 (.env):
    고령화/.env 파일에 아래 한 줄을 추가:
        KOSIS_API_KEY=발급받은_인증키
"""

import os
import requests
import pandas as pd
import time


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

# ============================================================
# CONFIG
# ============================================================

KOSIS_API_KEY = os.environ.get("KOSIS_API_KEY")
if not KOSIS_API_KEY:
    raise RuntimeError(
        "KOSIS_API_KEY가 설정되지 않았습니다. 고령화/.env 파일에 "
        "KOSIS_API_KEY=발급받은_인증키 를 추가하세요."
    )

START_YEAR = "2015"
END_YEAR = "2024"

# 지표명 -> (orgId, tblId, 분류축 개수) 매핑
# DT_1YL20631 에 총인구수·65세이상인구수·고령인구비율이 모두 포함되어 있어
# 주민등록인구현황(DT_1B040A3)은 별도로 받지 않아도 됨.
#
# 분류축 개수: KOSIS 통계표는 지역 외에 급여종류 등 추가 분류축을 가질 수 있음.
# objL1만으로 부족하면 (err:20, objL) 오류가 나며, 이 경우 objL2, objL3...을
# 순서대로 추가해야 함. 아래 숫자는 필요한 objL 개수(objL1, objL2, ... objLn).
KOSIS_TABLES = {
    "고령인구비율": ("101", "DT_1YL20631", 1),
    "장기요양기관현황": ("350", "DT_35006_N019", 2),  # objL1, objL2 모두 필요
    # 기획서 2.1에 수집 대상으로 명시됐으나 누락돼 있던 항목 (2026-08-24 (3) 추가).
    # 총병상수(A)/주민등록인구(B)/인구 천명당 병상수(A÷B×1000) 3개 항목 포함.
    "의료기관병상수": ("101", "DT_1YL20971", 1),
}


# ============================================================
# 수집 함수
# ============================================================

def fetch_kosis(org_id: str, tbl_id: str, start_year: str, end_year: str,
                 obj_l_count: int = 1) -> pd.DataFrame:
    """KOSIS Open API에서 시도 단위 통계자료를 JSON으로 받아 DataFrame으로 반환."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": KOSIS_API_KEY,
        "itmId": "ALL",         # 항목 전체
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",           # 연간 자료
        "startPrdDe": start_year,
        "endPrdDe": end_year,
        "orgId": org_id,
        "tblId": tbl_id,
    }
    # objL1, objL2, ... objLn 을 모두 ALL로 채움 (통계표의 분류축 개수만큼)
    for i in range(1, obj_l_count + 1):
        params[f"objL{i}"] = "ALL"

    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    res.encoding = "utf-8"      # 인코딩 자동감지로 인한 지연 방지
    data = res.json()

    if isinstance(data, dict) and "err" in data:
        raise RuntimeError(f"KOSIS API 오류: {data}")

    df = pd.DataFrame(data)
    # KOSIS 표준 응답 필드: C1_NM(지역명), C2_NM(2번째 분류축 - 있는 경우만), PRD_DE(연도),
    # DT(수치값), ITM_NM(항목명).
    # [버그, 2026-08-24 (3)] C2_NM을 버리면 장기요양기관현황처럼 분류축이 2개인 통계표에서
    # "계(합계)"와 세부 시설유형(방문요양/노인요양시설 등) 행이 같은 item명으로 뭉개져
    # region+year+item 기준으로 봤을 때 가짜 중복행이 생긴다. C2_NM이 있으면 반드시 살려서
    # 전처리 단계에서 "계" 행만 골라 쓸 수 있게 한다.
    keep_cols = [c for c in ["C1_NM", "C2_NM", "PRD_DE", "ITM_NM", "DT"] if c in df.columns]
    df = df[keep_cols].rename(columns={
        "C1_NM": "region", "C2_NM": "category2", "PRD_DE": "year", "ITM_NM": "item", "DT": "value"
    })

    # item 컬럼의 HTML 줄바꿈 태그 제거
    if "item" in df.columns:
        df["item"] = (
            df["item"]
            .str.replace("＜br＞", "", regex=False)
            .str.replace("<br>", "", regex=False)
        )

    return df


def collect_all_kosis() -> dict:
    results = {}
    for name, (org_id, tbl_id, obj_l_count) in KOSIS_TABLES.items():
        print(f"[KOSIS] 수집 중: {name} (orgId={org_id}, tblId={tbl_id}, objL 개수={obj_l_count})")
        try:
            df = fetch_kosis(org_id, tbl_id, START_YEAR, END_YEAR, obj_l_count)
            results[name] = df
            time.sleep(1)  # 과도한 연속 호출 방지
        except Exception as e:
            print(f"  -> 실패: {e}")
            if "err': '20'" in str(e) or "'20'" in str(e):
                print(f"     -> objL 관련 오류입니다. KOSIS_TABLES에서 '{name}'의 objL 개수를 "
                      f"{obj_l_count + 1}로 늘려서 다시 시도해보세요.")
    return results


# ============================================================
# 실행부
# ============================================================

if __name__ == "__main__":
    print("=== KOSIS 데이터 수집 시작 ===")
    data = collect_all_kosis()
    for name, df in data.items():
        out_path = f"../data/raw/kosis_{name}.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {out_path} ({len(df)} rows)")
        print(df.head())
        if "item" in df.columns:
            print("포함된 항목 목록:", df["item"].unique()[:20])
