# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 05_지역별_고령화율_TOP10.png
# (원본 소스: scripts/visualize_feedback_0827_2.py의 fig_22_region_top10_only)
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


def country_legend(ax, **kwargs):
    from matplotlib.lines import Line2D
    proxies = [Line2D([0], [0], marker="s", linestyle="", markersize=10,
                       markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE)
               for c in ("KR", "JP")]
    ax.legend(proxies, [COUNTRY_LABEL[c] for c in ("KR", "JP")],
              frameon=False, fontsize=9, labelcolor="#52514e", **kwargs)


# --- dataset: country, region_name_kr, year(2023만), aging_rate ---
top10 = dataset.sort_values("aging_rate", ascending=False).head(10)
top10 = top10.iloc[::-1]  # barh는 아래부터 그려지므로 뒤집어야 1위가 맨 위

labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n in zip(top10["country"], top10["region_name_kr"])]
vals = list(top10["aging_rate"])
colors = [COUNTRY_COLOR[c] for c in top10["country"]]

fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
bars = ax.barh(labels, vals, color=colors, height=0.6)
for b, v in zip(bars, vals):
    ax.text(v + 0.4, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
            va="center", fontsize=9, color=INK_PRIMARY)
style_ax(ax, y_grid=False, x_grid=True)
ax.set_xlim(0, max(vals) * 1.15)
ax.set_title("지역별 고령화율 TOP 10 (2023, 64개 지역 중)", fontsize=12.5,
             color=INK_PRIMARY, loc="left", fontweight="bold")
country_legend(ax, loc="lower right")
fig.tight_layout()
plt.show()
