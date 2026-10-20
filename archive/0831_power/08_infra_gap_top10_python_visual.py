# ============================================================
# Power BI "Python 시각적 개체"에 붙여넣는 코드
# → 최종선정그래프 07_국가내_인프라확충_시급지역_TOP10.png
# (원본 소스: scripts/visualize.py의 fig_08_infra_gap_ranking)
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
#     단위로 값을 합쳐서 넘겨버려 아래 코드의 지역별 순위 계산이 틀어집니다.
#     모든 집계(순위·평균·합계)는 이 코드 안에서 pandas로 직접 계산합니다.
#
# ▶ 시각적 개체 필터에 Dim_Date[year]를 넣고 "2023"만 남기세요.
#
# ▶ Power BI가 자동으로 만들어주는 아래 두 줄(전처리 preamble)은 건드리지 말고
#   그 아래에 이 파일의 내용을 그대로 붙여넣으면 됩니다:
#     # dataset = pandas.DataFrame(...)
#     # dataset = dataset.drop_duplicates()
#
# ------------------------------------------------------------
# ▶ 발표용 안내: 이 코드는 아래 6개 블록으로 나뉘어 있습니다.
#   블록 0. 준비물 (라이브러리 + 디자인 설정)      — 발표 땐 한 줄로 넘어가도 됨
#   블록 1. 데이터 정리 (결측치 제외 + 인프라 밀도 계산)
#   블록 2. 순위 매기기 (나라 안에서 고령화율 순위 vs 인프라 순위)
#   블록 3. 격차지수 계산 + TOP10 뽑기
#   블록 4. 그래프 그리기 (막대 + 숫자 라벨)
#   블록 5. 꾸미기 (제목 · 범례 · 각주)
# ============================================================


# ============================================================
# 블록 0. 준비물 — 라이브러리 + 그래프 디자인 설정
#   (발표 때는 "한글 깨짐 방지 + 색상 팔레트 설정"이라고만 짧게 언급하면 됨)
# ============================================================
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 등록 (Windows 기본 폰트인 맑은 고딕을 강제로 사용)
try:
    fm.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
except Exception:
    pass
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

# 색상 팔레트 — 한국=파랑, 일본=주황으로 통일 (다른 그래프들과 색 맞춤)
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
COUNTRY_COLOR = {"KR": "#2a78d6", "JP": "#eb6834"}
COUNTRY_LABEL = {"KR": "한국", "JP": "일본"}


def style_ax(ax, x_grid=False, y_grid=True):
    """축 테두리·격자선을 다듬는 도우미 함수 (그래프마다 반복 사용)"""
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
    """오른쪽 위 '한국/일본' 범례를 그려주는 도우미 함수"""
    from matplotlib.lines import Line2D
    proxies = [Line2D([0], [0], marker="s", linestyle="", markersize=10,
                       markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE)
               for c in ("KR", "JP")]
    ax.legend(proxies, [COUNTRY_LABEL[c] for c in ("KR", "JP")],
              frameon=False, fontsize=9, labelcolor="#52514e", **kwargs)


# ============================================================
# 블록 1. 데이터 정리
#   병상수·요양기관수 둘 중 하나라도 비어있는 지역은 계산에서 빼고,
#   "인프라 밀도" = 병상수(인구 1만명당) + 요양기관수(인구 1만명당) 를 새로 만든다.
#   → 발표 멘트 예: "병상수와 요양기관수, 두 인프라 지표를 하나로 합쳐서
#     '인프라 밀도'라는 지표를 새로 만들었습니다"
# ============================================================
# dataset: country, region_name_kr, year(2023만), aging_rate,
#          medical_beds_per_10k, care_facility_per_10k
df = dataset[dataset["medical_beds_per_10k"].notna() & dataset["care_facility_per_10k"].notna()].copy()
df["infra_density"] = df["medical_beds_per_10k"] + df["care_facility_per_10k"]


# ============================================================
# 블록 2. 순위 매기기
#   "나라 안에서" 순위를 매긴다는 게 핵심 — 한국·일본을 섞어서 순위를 매기면
#   원래 고령화율·인프라 수준이 높은 일본이 순위를 다 차지해버리기 때문에,
#   groupby("country")로 한국 안에서 따로, 일본 안에서 따로 순위를 매긴다.
#   (Power BI DAX의 RANKX(ALLEXCEPT(...,country), ...) 와 정확히 같은 계산)
#   → 발표 멘트 예: "고령화율 순위와 인프라 순위, 이 두 순위를 각각 나라
#     안에서 따로 매겼습니다"
# ============================================================
df["aging_rank"] = df.groupby("country")["aging_rate"].rank(method="min", ascending=False)
df["infra_rank"] = df.groupby("country")["infra_density"].rank(method="min", ascending=False)


# ============================================================
# 블록 3. 격차지수 계산 + TOP10 뽑기
#   격차지수 = 고령화율 순위 - 인프라 순위
#   → 이 값이 음수로 클수록 "고령화는 심한데 인프라 순위는 낮은" 지역,
#     즉 인프라 확충이 가장 시급한 지역이라는 뜻.
#   → 발표 멘트 예: "고령화율 순위에서 인프라 순위를 뺀 걸 '격차지수'로
#     정의했고, 이 값이 음수로 클수록 인프라 확충이 시급한 지역입니다"
#
#   그 다음 한국·일본 각각 격차지수가 가장 작은(=가장 시급한) 10개 지역을
#   뽑아서 하나로 합친다.
# ============================================================
df["gap"] = (df["aging_rank"] - df["infra_rank"]).astype(int)

kr_top = df[df["country"] == "KR"].sort_values("gap").head(10)
jp_top = df[df["country"] == "JP"].sort_values("gap").head(10)
combined = pandas.concat([kr_top, jp_top]).sort_values("gap", ascending=True)
combined = combined.iloc[::-1]  # barh는 아래부터 그려지므로 뒤집어야 1위가 맨 위


# ============================================================
# 블록 4. 그래프 그리기 — 가로 막대(barh) + 막대 끝에 숫자 라벨
#   → 발표 멘트 예: "막대 하나가 지역 하나이고, 막대 끝의 숫자가
#     방금 계산한 격차지수입니다. 파란색이 한국, 주황색이 일본입니다"
# ============================================================
labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n in zip(combined["country"], combined["region_name_kr"])]
vals = list(combined["gap"])
colors = [COUNTRY_COLOR[c] for c in combined["country"]]

fig, ax = plt.subplots(figsize=(8, 8.5), facecolor=SURFACE)
bars = ax.barh(labels, vals, color=colors, height=0.65)
xmin, xmax = min(vals), max(vals)
for b, v in zip(bars, vals):
    ax.text(v - abs(xmin) * 0.02 if v < 0 else v + abs(xmin) * 0.02,
            b.get_y() + b.get_height() / 2, f"{v}",
            va="center", ha="right" if v < 0 else "left", fontsize=8.5, color=INK_PRIMARY)


# ============================================================
# 블록 5. 꾸미기 — 제목 · 범례 · 각주
#   → 발표 멘트 예: "아래 각주에 격차지수가 정확히 뭘 계산한 값인지
#     한 줄로 설명을 붙여놨습니다"
# ============================================================
style_ax(ax, y_grid=False, x_grid=True)
ax.set_xlim(xmin * 1.2, abs(xmin) * 0.25)
ax.set_title("국가 내 인프라 확충 시급 지역 TOP 10 (2023, 국가별 인프라 격차지수)",
             fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold")
country_legend(ax, loc="upper right")
fig.text(0.02, 0.01,
         "인프라 격차지수 = (국가 내) 고령화율 순위 - (병상수+요양기관수)순위. 더 음수일수록 그 나라 안에서 고령화 대비 인프라가 부족한 지역.\n"
         "한국은 지역 수가 17개뿐이라 TOP10에 0 이상 값도 일부 포함됨.",
         fontsize=7.5, color=INK_MUTED, ha="left", va="bottom")
fig.tight_layout(rect=(0, 0.06, 1, 0.94))
plt.show()
