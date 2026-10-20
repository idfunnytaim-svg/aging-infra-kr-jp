# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드 — 12. 슬로프 차트
# (2015→2023 고령화율 변화, 주목 지역 9곳 강조)
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
# ▶ 시각적 개체 필터(Filters on this visual)에 Dim_Date[year]를 넣고
#   "2015, 2023"만 남도록 필터링하세요 (다른 연도는 빼야 함).
#
# ▶ Power BI가 자동으로 만들어주는 아래 두 줄(전처리 preamble)은 건드리지 말고
#   그 아래에 이 파일의 내용을 그대로 붙여넣으면 됩니다:
#     # dataset = pandas.DataFrame(...)
#     # dataset = dataset.drop_duplicates()
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

# --- 한글 폰트 (Windows: 맑은 고딕 기본 내장) ---
try:
    fm.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
except Exception:
    pass
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

# --- dataviz 팔레트 (기존 scripts/visualize.py와 동일) ---
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
    proxies = [Line2D([0], [0], marker="s", linestyle="", markersize=10,
                       markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE)
               for c in ("KR", "JP")]
    ax.legend(proxies, [COUNTRY_LABEL[c] for c in ("KR", "JP")],
              frameon=False, fontsize=9, labelcolor=INK_SECONDARY, **kwargs)


# --- dataset: country, region_name_kr, year(2015/2023만), aging_rate ---
pivot = (dataset.pivot_table(index=["country", "region_name_kr"],
                              columns="year", values="aging_rate")
         .reset_index().rename(columns={2015: "y15", 2023: "y23"}))
pivot["delta"] = pivot["y23"] - pivot["y15"]
pivot = pivot.sort_values("delta", ascending=False)

kr_top6 = pivot[pivot["country"] == "KR"].head(6)
jp_top2 = pivot[pivot["country"] == "JP"].head(2)
sejong = pivot[pivot["region_name_kr"] == "세종특별자치시"]
highlight = pandas.concat([kr_top6, jp_top2, sejong]).drop_duplicates(subset=["region_name_kr"])
highlight_names = set(highlight["region_name_kr"])

fig, ax = plt.subplots(figsize=(7.5, 7), facecolor=SURFACE)

# 배경: 나머지 지역은 옅은 회색 선
bg = pivot[~pivot["region_name_kr"].isin(highlight_names)]
for _, row in bg.iterrows():
    ax.plot([2015, 2023], [row["y15"], row["y23"]], color=BASELINE,
            linewidth=0.8, alpha=0.5, zorder=1)

for _, row in highlight.iterrows():
    c, n, y15, y23, delta = row["country"], row["region_name_kr"], row["y15"], row["y23"], row["delta"]
    ax.plot([2015, 2023], [y15, y23], color=COUNTRY_COLOR[c],
            linewidth=2.4, marker="o", markersize=5,
            markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE, zorder=3)
    ax.text(2023 + 0.15, y23, f"{n} (+{delta:.1f}%p)", fontsize=8.5,
            va="center", color=INK_PRIMARY)

style_ax(ax, y_grid=True)
ax.set_xlim(2014.7, 2026.5)
ax.set_xticks([2015, 2023])
ax.set_xlabel("")
ax.set_ylabel("고령화율(%)", fontsize=9, color=INK_SECONDARY,
              rotation=0, ha="right", va="bottom")
ax.yaxis.set_label_coords(-0.02, 1.03)
ax.set_title("슬로프 차트 — 2015→2023 고령화율 변화 (주목 지역 강조)",
             fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
country_legend(ax, loc="upper left")
fig.text(0.02, 0.01,
         "굵은 선=한국 증가폭 TOP6 + 일본 증가폭 TOP2(아오모리·아키타) + 세종(한국 최저, 대조군). 가는 회색 선=나머지 지역.",
         fontsize=7.5, color=INK_MUTED, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 1))
plt.show()
