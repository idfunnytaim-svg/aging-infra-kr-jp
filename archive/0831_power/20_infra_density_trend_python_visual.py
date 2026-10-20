# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 03_연도별_인프라밀도_추이.png
# (원본 소스: scripts/visualize_feedback_0827_2.py의 fig_20_infra_density_trend)
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
#     단위로 값을 SUM으로 합쳐서 넘겨버려 아래 코드의 "지역 평균" 계산이
#     틀어집니다(한국 17개·일본 47개로 지역 수가 달라 합계와 평균이 다름).
#     평균은 이 코드 안에서 pandas로 직접 계산합니다.
#
# ▶ 이 차트는 연도 필터를 걸지 않습니다 — 2015~2023 전체 연도가 있어야
#   추이(선)를 그릴 수 있습니다.
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
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
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
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    if y_grid:
        ax.yaxis.grid(True, color=GRIDLINE, linewidth=1)
        ax.set_axisbelow(True)
    if x_grid:
        ax.xaxis.grid(True, color=GRIDLINE, linewidth=1)


def country_legend(ax, **kwargs):
    from matplotlib.lines import Line2D
    proxies = [Line2D([0], [0], marker="s", linestyle="", markersize=10,
                       markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE)
               for c in ("KR", "JP")]
    ax.legend(proxies, [COUNTRY_LABEL[c] for c in ("KR", "JP")],
              frameon=False, fontsize=9, labelcolor=INK_SECONDARY, **kwargs)


# --- dataset: country, region_name_kr, year(전체), medical_beds_per_10k, care_facility_per_10k ---
agg = dataset.groupby(["country", "year"], as_index=False)[
    ["medical_beds_per_10k", "care_facility_per_10k"]
].mean()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=SURFACE)
for ax, col, title, ylabel in [
    (ax1, "medical_beds_per_10k", "인구 1만명당 병상수 추이", "병상수/1만명"),
    (ax2, "care_facility_per_10k", "인구 1만명당 요양기관수 추이", "요양기관수/1만명"),
]:
    for country in ("KR", "JP"):
        sub = agg[agg["country"] == country].sort_values("year")
        ax.plot(sub["year"], sub[col], color=COUNTRY_COLOR[country], linewidth=2,
                marker="o", markersize=4.5, markerfacecolor=COUNTRY_COLOR[country],
                markeredgecolor=SURFACE, markeredgewidth=1)
    style_ax(ax)
    ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
country_legend(ax1, loc="lower right")
fig.suptitle("연도별 인프라밀도 추이 (2015~2023)", fontsize=12.5,
             color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.92))
plt.show()
