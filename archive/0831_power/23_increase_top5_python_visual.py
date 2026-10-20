# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 08_고령화율_증가폭_국가별TOP5.png
# (원본 소스: scripts/visualize_feedback_0827_2.py의 fig_23_increase_top5_by_country)
#
# ▶ 준비 (필드 창에 이 순서로 드래그하고, 각 필드 이름을 아래 표대로 바꾸세요
#    — 필드 칩을 더블클릭하면 표시 이름을 바꿀 수 있습니다):
#
#   드래그할 필드                              → 표시 이름(rename)
#   ------------------------------------------  --------------------
#   Dim_Region[country]                         → country
#   Dim_Region[region_name_kr]                  → region_name_kr
#   Dim_Date[year]                               → year
#   Fact_RegionStats[aging_rate]                → aging_rate
#
# ▶ 시각적 개체 필터에 Dim_Date[year]를 넣고 "2015, 2023"만 남기세요.
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


# --- dataset: country, region_name_kr, year(2015/2023만), aging_rate ---
pivot = (dataset.pivot_table(index=["country", "region_name_kr"],
                              columns="year", values="aging_rate")
         .reset_index().rename(columns={2015: "y15", 2023: "y23"}))
pivot["delta"] = pivot["y23"] - pivot["y15"]
pivot = pivot.sort_values(["country", "delta"], ascending=[True, False])

kr_top5 = pivot[pivot["country"] == "KR"].head(5)
jp_top5 = pivot[pivot["country"] == "JP"].head(5)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE)
for ax, subset, country, title in [
    (ax1, kr_top5, "KR", "한국 TOP5"), (ax2, jp_top5, "JP", "일본 TOP5"),
]:
    subset = subset.iloc[::-1]
    labels = list(subset["region_name_kr"])
    vals = list(subset["delta"])
    bars = ax.barh(labels, vals, color=COUNTRY_COLOR[country], height=0.55)
    for b, v in zip(bars, vals):
        ax.text(v + 0.08, b.get_y() + b.get_height() / 2, f"+{v:.1f}%p",
                va="center", fontsize=9, color=INK_PRIMARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(0, max(vals) * 1.3)
    ax.set_title(title, fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
fig.suptitle("2015→2023 고령화율 증가폭 — 국가별 TOP5",
             fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.9))
plt.show()
