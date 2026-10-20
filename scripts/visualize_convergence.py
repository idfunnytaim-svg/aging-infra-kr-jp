"""개인 보고서 5.3절(집계 수준) 근거 그래프 3종.
팀 공동 산출물(figures/, powerbi/)에는 없는 개인 관점 분석이라 개인보고서/그래프/에 저장한다.
색상·스타일은 scripts/visualize.py의 팔레트·규칙을 그대로 재사용(팀 그래프와 시각적 통일감 유지).

1. 01_sigma_convergence_combined.png — 국가 간(통합) 시그마수렴: 연도별 결합 표준편차 추이
2. 02_sigma_divergence_within.png    — 국가 내부 시그마발산: 국가별 연도별 표준편차 추이
3. 03_beta_divergence_scatter.png    — 베타수렴 검정: 2015년 초기 고령화율 × 2015~2023 증가기울기 산점도
"""
import sqlite3
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
OUT_DIR = BASE / "개인보고서" / "그래프"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
fm.fontManager.addfont(FONT_PATH)
plt.rcParams["font.family"] = fm.FontProperties(fname=FONT_PATH).get_name()
plt.rcParams["axes.unicode_minus"] = False

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


def load_df(con):
    q = """
        SELECT r.region_id, r.country, r.region_name_kr, d.year, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
    """
    return pd.read_sql(q, con)


# ============================================================
# 1. 국가 간(통합) 시그마수렴
# ============================================================

def fig_01_sigma_combined(df):
    combined = df.groupby("year")["aging_rate"].std()

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
    ax.plot(combined.index, combined.values, color=INK_PRIMARY, linewidth=2.4,
            marker="o", markersize=5)
    ax.fill_between(combined.index, combined.values, combined.values.min(),
                     color=INK_MUTED, alpha=0.08)

    start, end = combined.iloc[0], combined.iloc[-1]
    ax.annotate(f"{start:.2f}%p", (combined.index[0], start), textcoords="offset points",
                xytext=(-8, 10), fontsize=9.5, color=INK_SECONDARY, ha="right", fontweight="bold")
    ax.annotate(f"{end:.2f}%p", (combined.index[-1], end), textcoords="offset points",
                xytext=(8, -14), fontsize=9.5, color=INK_SECONDARY, ha="left", fontweight="bold")

    style_ax(ax)
    ax.set_xticks(combined.index)
    ax.set_ylabel("64개 지역 고령화율 표준편차 (%p)", fontsize=9.5, color=INK_SECONDARY)
    ax.set_title("국가 간(통합) 시그마수렴 — 64개 지역 전체의 격차는 좁혀지고 있다",
                 fontsize=12, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.text(0.02, 0.02,
              "출처: data/aging_infra.db 직접 쿼리(Fact_RegionStats, 2015~2023) — 매년 64개 지역 고령화율의 표준편차",
              fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_DIR / "01_sigma_convergence_combined.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


# ============================================================
# 2. 국가 내부 시그마발산
# ============================================================

def fig_02_sigma_within(df):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
    for c in ("KR", "JP"):
        sub = df[df.country == c].groupby("year")["aging_rate"].std()
        ax.plot(sub.index, sub.values, color=COUNTRY_COLOR[c], linewidth=2.4,
                marker="o", markersize=5, label=COUNTRY_LABEL[c])
        ax.annotate(f"{sub.iloc[-1]:.2f}", (sub.index[-1], sub.iloc[-1]),
                    textcoords="offset points", xytext=(8, 0), fontsize=9.5,
                    color=COUNTRY_COLOR[c], ha="left", fontweight="bold")

    style_ax(ax)
    ax.set_xticks(sorted(df["year"].unique()))
    ax.set_ylabel("국가 내 지역별 고령화율 표준편차 (%p)", fontsize=9.5, color=INK_SECONDARY)
    ax.set_title("국가 내부 시그마발산 — 같은 나라 안에서는 지역 간 격차가 오히려 벌어진다",
                 fontsize=12, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, loc="upper left")
    fig.text(0.02, 0.02,
              "출처: data/aging_infra.db 직접 쿼리 — 국가별로 나눠 매년 지역 간 고령화율 표준편차 계산",
              fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_DIR / "02_sigma_divergence_within.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


# ============================================================
# 3. 베타수렴 검정 산점도
# ============================================================

def fig_03_beta_scatter(df):
    def slope(g):
        return np.polyfit(g["year"].values, g["aging_rate"].values, 1)[0]

    res = (
        df.groupby(["region_id", "country", "region_name_kr"])
        .apply(slope)
        .reset_index(name="slope")
    )
    init = df[df.year == df.year.min()][["region_id", "aging_rate"]].rename(
        columns={"aging_rate": "init"}
    )
    res = res.merge(init, on="region_id")

    fig, ax = plt.subplots(figsize=(8.5, 5.5), facecolor=SURFACE)
    for c in ("KR", "JP"):
        sub = res[res.country == c]
        ax.scatter(sub["init"], sub["slope"], color=COUNTRY_COLOR[c], alpha=0.75,
                   s=46, edgecolor=SURFACE, linewidth=0.6, label=COUNTRY_LABEL[c])
        b, a = np.polyfit(sub["init"], sub["slope"], 1)
        xs = np.linspace(sub["init"].min(), sub["init"].max(), 50)
        ax.plot(xs, a + b * xs, color=COUNTRY_COLOR[c], linewidth=1.6, linestyle="--", alpha=0.85)
        r = np.corrcoef(sub["init"], sub["slope"])[0, 1]
        ax.annotate(f"{COUNTRY_LABEL[c]} r={r:.2f}", xy=(xs[-1], a + b * xs[-1]),
                    xytext=(6, 0), textcoords="offset points", fontsize=9.5,
                    color=COUNTRY_COLOR[c], fontweight="bold", va="center")

    for label in ("부산광역시", "세종특별자치시", "도쿄도"):
        row = res[res.region_name_kr == label]
        if not row.empty:
            x, y = row["init"].values[0], row["slope"].values[0]
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(0, 10),
                        fontsize=8.5, color=INK_PRIMARY, ha="center", fontweight="bold")

    style_ax(ax, x_grid=True)
    ax.axhline(0, color=BASELINE, linewidth=1)
    ax.set_xlabel("2015년 초기 고령화율 (%)", fontsize=9.5, color=INK_SECONDARY)
    ax.set_ylabel("2015~2023 고령화율 증가기울기 (%p/년)", fontsize=9.5, color=INK_SECONDARY)
    ax.set_title("베타수렴 검정 — 원래 높던 지역이 더 빠르게 늙고 있다(양의 상관 = 발산)",
                 fontsize=12, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, loc="lower right")
    fig.text(0.02, 0.02,
              "출처: data/aging_infra.db 직접 쿼리 — 지역별 회귀직선 기울기(np.polyfit) × 2015년 초기값, 점선은 국가별 추세선",
              fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_DIR / "03_beta_divergence_scatter.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)

    return res


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    df = load_df(con)
    fig_01_sigma_combined(df)
    fig_02_sigma_within(df)
    res = fig_03_beta_scatter(df)
    con.close()
    print("saved to", OUT_DIR)
    print(res.sort_values("slope", ascending=False).to_string(index=False))
