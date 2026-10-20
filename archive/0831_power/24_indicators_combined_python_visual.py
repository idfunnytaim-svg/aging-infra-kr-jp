# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 01_국가별_고령화인프라지표_막대.png
# (원본 소스: scripts/visualize_final_selection.py의 fig_24_indicators_combined)
#
# ▶ 준비 (필드 창에 이 순서로 드래그하고, 각 필드 이름을 아래 표대로 바꾸세요
#    — 필드 칩을 더블클릭하면 표시 이름을 바꿀 수 있습니다):
#
#   드래그할 필드                              → 표시 이름(rename)
#   ------------------------------------------  --------------------
#   Dim_Region[country]                         → country
#   Dim_Region[region_name_kr]                  → region_name_kr   (★ 반드시 넣기)
#   Dim_Date[year]                               → year
#   Fact_RegionStats[aging_rate]                → aging_rate
#   Fact_RegionStats[medical_beds_per_10k]      → medical_beds_per_10k
#   Fact_RegionStats[care_facility_per_10k]     → care_facility_per_10k
#
#   ★ region_name_kr을 꼭 넣어야 하는 이유: 이걸 빼면 Power BI가 country
#     단위로 값을 SUM으로 합쳐서 넘겨버려 아래 코드의 "국가 평균" 계산이
#     틀어집니다. 평균은 이 코드 안에서 pandas로 직접 계산합니다.
#
# ▶ 시각적 개체 필터에 Dim_Date[year]를 넣고 "2023"만 남기세요.
#
# ▶ Power BI가 자동으로 만들어주는 아래 두 줄(전처리 preamble)은 건드리지 말고
#   그 아래에 이 파일의 내용을 그대로 붙여넣으면 됩니다:
#     # dataset = pandas.DataFrame(...)
#     # dataset = dataset.drop_duplicates()
# ============================================================

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
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
COUNTRY_COLOR = {"KR": "#2a78d6", "JP": "#eb6834"}
COUNTRY_LABEL = {"KR": "한국", "JP": "일본"}


def style_ax(ax, x_grid=False, y_grid=True):
    ax.set_facecolor(SURFACE)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BASELINE)
        ax.spines[spine].set_linewidth(1)
    ax.tick_params(colors="#898781", labelsize=9)
    if y_grid:
        ax.yaxis.grid(True, color=GRIDLINE, linewidth=1)
        ax.set_axisbelow(True)
    if x_grid:
        ax.xaxis.grid(True, color=GRIDLINE, linewidth=1)


# --- dataset: country, region_name_kr, year(2023만), aging_rate,
#              medical_beds_per_10k, care_facility_per_10k ---
agg = dataset.groupby("country", as_index=False)[
    ["aging_rate", "medical_beds_per_10k", "care_facility_per_10k"]
].mean()
data = {row["country"]: (row["aging_rate"], row["medical_beds_per_10k"], row["care_facility_per_10k"])
        for _, row in agg.iterrows()}
countries = ["KR", "JP"]

metrics = [
    ("평균 고령화율", 0, "{:.1f}%"),
    ("인구 1만명당 병상수", 1, "{:.1f}"),
    ("인구 1만명당 요양기관수", 2, "{:.2f}"),
]

fig, axes = plt.subplots(1, 3, figsize=(11, 4.3), facecolor=SURFACE)
for ax, (title, idx, fmt) in zip(axes, metrics):
    vals = [data[c][idx] for c in countries]
    bars = ax.bar([COUNTRY_LABEL[c] for c in countries], vals,
                  color=[COUNTRY_COLOR[c] for c in countries], width=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, fmt.format(v),
                ha="center", fontsize=10.5, color=INK_PRIMARY, fontweight="bold")
    style_ax(ax, y_grid=True)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_title(title, fontsize=10.5, color=INK_PRIMARY, loc="left", fontweight="bold")
fig.suptitle("국가별 고령화·인프라 지표 (2023, 한국·일본 통합 비교)", fontsize=12.5,
             color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.90))
plt.show()
