# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 06_국가별_의료돌봄_구성비_도넛.png
# (원본 소스: scripts/visualize_final_selection.py의 fig_25_medical_care_donut)
#
# ▶ 준비 (필드 창에 이 순서로 드래그하고, 각 필드 이름을 아래 표대로 바꾸세요
#    — 필드 칩을 더블클릭하면 표시 이름을 바꿀 수 있습니다):
#
#   드래그할 필드                              → 표시 이름(rename)
#   ------------------------------------------  --------------------
#   Dim_Region[country]                         → country
#   Dim_Region[region_name_kr]                  → region_name_kr   (★ 반드시 넣기)
#   Dim_Date[year]                               → year
#   Fact_RegionStats[medical_beds_per_10k]      → medical_beds_per_10k
#   Fact_RegionStats[care_facility_per_10k]     → care_facility_per_10k
#
#   ★ region_name_kr을 꼭 넣어야 하는 이유: 이걸 빼면 Power BI가 country
#     단위로 값을 먼저 합쳐서 넘겨버릴 수 있습니다. 국가별 합계(SUM)는
#     이 코드 안에서 pandas로 직접 계산합니다.
#
# ▶ 시각적 개체 필터에 Dim_Date[year]를 넣고 "2023"만 남기세요.
#
# ▶ 주의: 한국 "장기요양기관수"(전체 서비스유형 합)와 일본 "개호노인복지시설수"
#   (입소시설 1종류)는 정의 범위가 달라 국가 간 절대량 비교가 아닙니다 —
#   국가 내부 구성비만 참고하세요(그래프 하단 캡션에도 명시됨).
#
# ▶ Power BI가 자동으로 만들어주는 아래 두 줄(전처리 preamble)은 건드리지 말고
#   그 아래에 이 파일의 내용을 그대로 붙여넣으면 됩니다:
#     # dataset = pandas.DataFrame(...)
#     # dataset = dataset.drop_duplicates()
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 한글 폰트 (Windows: 맑은 고딕 기본 내장) ---
try:
    fm.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
except Exception:
    pass
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

# --- dataviz 팔레트 ---
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_MUTED = "#898781"
COUNTRY_COLOR = {"KR": "#2a78d6", "JP": "#eb6834"}
COUNTRY_LABEL = {"KR": "한국", "JP": "일본"}


# --- dataset: country, region_name_kr, year(2023만), medical_beds_per_10k, care_facility_per_10k ---
agg = dataset.groupby("country", as_index=False)[["medical_beds_per_10k", "care_facility_per_10k"]].sum()
data = {row["country"]: (row["medical_beds_per_10k"], row["care_facility_per_10k"])
        for _, row in agg.iterrows()}
BEDS_COLOR, CARE_COLOR = "#2a78d6", "#eda100"

fig, axes = plt.subplots(1, 2, figsize=(9, 5), facecolor=SURFACE)
for ax, country in zip(axes, ("KR", "JP")):
    beds, care = data[country]
    total = beds + care
    vals = [beds, care]
    labels = [f"병상수\n{beds/total*100:.0f}%", f"요양기관수\n{care/total*100:.0f}%"]
    wedges, texts = ax.pie(
        vals, colors=[BEDS_COLOR, CARE_COLOR], startangle=90,
        wedgeprops=dict(width=0.42, edgecolor=SURFACE, linewidth=2),
    )
    for i, w in enumerate(wedges):
        ang = (w.theta2 + w.theta1) / 2
        x, y = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        ax.text(x * 0.78, y * 0.78, labels[i], ha="center", va="center",
                fontsize=9, color="white" if i == 0 else INK_PRIMARY, fontweight="bold")
    ax.text(0, 0, COUNTRY_LABEL[country], ha="center", va="center", fontsize=13,
            color=COUNTRY_COLOR[country], fontweight="bold")
    ax.set_title(f"{COUNTRY_LABEL[country]} (2023)", fontsize=11,
                 color=INK_PRIMARY, fontweight="bold")
fig.suptitle("국가별 의료 vs 돌봄 인프라 구성비", fontsize=12.5, color=INK_PRIMARY,
             x=0.02, ha="left", fontweight="bold")
fig.text(0.02, 0.02,
         "주의: 한국 '장기요양기관수'(전체 서비스유형 합)와 일본 '개호노인복지시설수'(입소시설 1종류)는 "
         "정의 범위가 달라 국가 간 절대량 비교가 아님 — 국가 내부 구성비만 참고.",
         fontsize=7.5, color=INK_MUTED, ha="left")
fig.tight_layout(rect=(0, 0.06, 1, 0.90))
plt.show()
