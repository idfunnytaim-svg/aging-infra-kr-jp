# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드 — 14. 범프 차트
# (2015~2023 고령화율 순위 흐름, 주목 지역 9곳 강조)
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
# ▶ 이 차트는 연도 필터를 걸지 않습니다 — 2015~2023 전체 연도가 다 있어야
#   순위(rank)를 해마다 계산할 수 있습니다.
#
# ▶ 원본(scripts/visualize_powerbi_ideas.py)의 RANKX 로직을 그대로
#   pandas의 groupby+rank로 재현합니다 — 결과는 SQL 버전과 동일합니다.
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


# --- dataset: country, region_name_kr, year(전체), aging_rate ---
YEARS = sorted(dataset["year"].unique())
n_regions = dataset["region_name_kr"].nunique()

# 연도별 고령화율 내림차순 순위 (1위=최고령) — DAX RANKX와 동일한 결과
dataset = dataset.copy()
dataset["rank"] = dataset.groupby("year")["aging_rate"].rank(ascending=False, method="first").astype(int)
rank_pivot = dataset.pivot_table(index="region_name_kr", columns="year", values="rank")

# 주목 지역 9곳: 한국 증가폭 TOP6 + 일본 증가폭 TOP2 + 세종(대조군)
p2 = (dataset[dataset["year"].isin([2015, 2023])]
      .pivot_table(index=["country", "region_name_kr"], columns="year", values="aging_rate")
      .reset_index().rename(columns={2015: "y15", 2023: "y23"}))
p2["delta"] = p2["y23"] - p2["y15"]
p2 = p2.sort_values("delta", ascending=False)
kr_top6 = p2[p2["country"] == "KR"].head(6)
jp_top2 = p2[p2["country"] == "JP"].head(2)
sejong = p2[p2["region_name_kr"] == "세종특별자치시"]
highlight = pandas.concat([kr_top6, jp_top2, sejong]).drop_duplicates(subset=["region_name_kr"])
countries = dict(zip(highlight["region_name_kr"], highlight["country"]))

fig, ax = plt.subplots(figsize=(9.5, 7.5), facecolor=SURFACE)
for n, c in countries.items():
    ranks = [rank_pivot.loc[n, y] for y in YEARS]
    ax.plot(YEARS, ranks, color=COUNTRY_COLOR[c], linewidth=2.2,
            marker="o", markersize=4, markerfacecolor=COUNTRY_COLOR[c],
            markeredgecolor=SURFACE, zorder=3)


# 라벨 겹침 방지: 최소 간격을 강제로 벌려서 배치
def spaced(items, min_gap=3.0):
    items = sorted(items)
    placed = []
    for rank, n, c in items:
        y = rank if not placed else max(rank, placed[-1] + min_gap)
        placed.append(y)
    return list(zip(items, placed))


ends_2023 = spaced([(rank_pivot.loc[n, 2023], n, c) for n, c in countries.items()])
ends_2015 = spaced([(rank_pivot.loc[n, 2015], n, c) for n, c in countries.items()])

for (rank, n, c), y in ends_2023:
    ax.plot([2023, 2023.35], [rank, y], color=BASELINE, linewidth=0.8, zorder=1)
    ax.text(2023.45, y, f"{n} ({rank}위)", fontsize=8.5, ha="left", va="center",
            color=INK_PRIMARY, fontweight="bold")
for (rank, n, c), y in ends_2015:
    ax.plot([2015, 2014.65], [rank, y], color=BASELINE, linewidth=0.8, zorder=1)
    ax.text(2014.55, y, n, fontsize=7.5, ha="right", va="center", color=INK_MUTED)

style_ax(ax, y_grid=True)
ax.invert_yaxis()
ax.set_xlim(2012.3, 2027.5)
ax.set_ylabel(f"고령화율 순위 ({n_regions}개 지역 중 1위=최고령)", fontsize=9,
              color=INK_SECONDARY, rotation=0, ha="right", va="bottom")
ax.yaxis.set_label_coords(-0.02, 1.03)
ax.set_title(f"범프 차트 — 주목 지역 9곳의 고령화율 순위 흐름 ({YEARS[0]}~{YEARS[-1]}, {n_regions}개 지역 중)",
             fontsize=12, color=INK_PRIMARY, loc="left", fontweight="bold")
country_legend(ax, loc="center left", bbox_to_anchor=(1.0, 0.5))
fig.text(0.02, 0.01,
         "한국 지역들이 해마다 순위를 끌어올리며 일본 지역 쪽으로 접근하는 모습을 보여준다 — Insight 1의 시각적 근거.",
         fontsize=7.5, color=INK_MUTED, ha="left")
fig.tight_layout(rect=(0, 0.03, 0.86, 1))
plt.show()
