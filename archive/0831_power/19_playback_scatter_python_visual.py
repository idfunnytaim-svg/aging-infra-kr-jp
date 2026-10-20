# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드 — 19. 재생축 산점도 필름스트립
# (2015·2019·2023년 고령화율×인프라밀도, 거품 크기=총인구)
#
# ⚠️ 참고: Power BI는 분산형(Scatter) 차트에 "재생 축(Play Axis)"이라는
#    기본 내장 기능이 있어서, 아래 필드만 그대로 드래그하면 코드 없이도
#    ▶버튼으로 2015→2023 애니메이션이 자동 재생됩니다 — 그게 더 화려하고
#    발표에도 좋으니, 정말 이 정지 이미지(필름스트립) 버전이 필요할 때만
#    이 스크립트를 쓰세요.
#      네이티브 재생축 버전: X축=aging_rate, Y축=medical_beds_per_10k
#      (+care_facility_per_10k를 더한 측정값 하나 새로 만들면 더 정확),
#      범례=country, 크기=total_pop, 재생 축=Dim_Date[year]
#
# ▶ 이 스크립트(정지 필름스트립)를 쓸 경우 준비:
#
#   드래그할 필드                              → 표시 이름(rename)
#   ------------------------------------------  --------------------
#   Dim_Region[country]                         → country
#   Dim_Date[year]                               → year
#   Fact_RegionStats[aging_rate]                → aging_rate
#   Fact_RegionStats[medical_beds_per_10k]      → medical_beds_per_10k
#   Fact_RegionStats[care_facility_per_10k]     → care_facility_per_10k
#   Fact_RegionStats[total_pop]                 → total_pop
#
# ▶ 시각적 개체 필터에 Dim_Date[year]를 넣고 "2015, 2019, 2023"만 남기세요.
#   (medical_beds_per_10k가 NULL인 행은 없어야 하니, 필요하면
#    "medical_beds_per_10k가 비어 있지 않음" 필터도 추가하세요.)
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

# --- dataviz 팔레트 (기존 scripts/visualize.py와 동일) ---
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
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
              frameon=False, fontsize=9, labelcolor=INK_SECONDARY, **kwargs)


# --- dataset: country, year(2015/2019/2023만), aging_rate,
#              medical_beds_per_10k, care_facility_per_10k, total_pop ---
dataset = dataset.copy()
dataset["infra"] = dataset["medical_beds_per_10k"] + dataset["care_facility_per_10k"]

years_present = sorted(dataset["year"].unique())
xlim = (dataset["aging_rate"].min() - 2, dataset["aging_rate"].max() + 2)
ylim = (dataset["infra"].min() - 5, dataset["infra"].max() + 15)
size_scale = 900 / dataset["total_pop"].max()

fig, axes = plt.subplots(1, len(years_present), figsize=(13, 4.6), facecolor=SURFACE, sharey=True)
if len(years_present) == 1:
    axes = [axes]
for ax, year in zip(axes, years_present):
    for country in ("KR", "JP"):
        sub = dataset[(dataset["year"] == year) & (dataset["country"] == country)]
        sizes = (sub["total_pop"] * size_scale).clip(lower=15)
        ax.scatter(sub["aging_rate"], sub["infra"], s=sizes, color=COUNTRY_COLOR[country],
                   alpha=0.55, edgecolor=SURFACE, linewidth=0.8, zorder=3)
    style_ax(ax)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_title(f"{year}년", fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.set_xlabel("고령화율(%)", fontsize=8.5, color=INK_SECONDARY)
axes[0].set_ylabel("인프라밀도(병상+요양기관/1만명)", fontsize=8.5, color=INK_SECONDARY)
country_legend(axes[-1], loc="upper right")
fig.suptitle("재생축 산점도 필름스트립 — 고령화율×인프라밀도의 시간에 따른 이동 (거품 크기=총인구)",
             fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
fig.text(0.02, 0.01,
         "Power BI 네이티브 재생 축(Play axis)을 쓰면 이 필름스트립이 매끄러운 애니메이션 1개로 자동 재생됩니다.",
         fontsize=7.5, color="#898781", ha="left")
fig.tight_layout(rect=(0, 0.05, 1, 0.90))
plt.show()
