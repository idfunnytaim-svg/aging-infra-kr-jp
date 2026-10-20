"""Power BI 없이도 결과를 보여줄 수 있는 Python 백업 대시보드.
docs/기획서.md 3.5(Page 1~3) 구성을 정적 이미지로 재현한다.
색은 dataviz 스킬의 검증된 팔레트를 사용 — 국가는 2개뿐이라 카테고리 순서
슬롯1(블루)=한국, 슬롯2(오렌지)=일본으로 전 그래프에서 고정한다.
"""
import sqlite3
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
FIG_DIR = BASE / "figures"
FIG_DIR.mkdir(exist_ok=True)

# --- 한글 폰트 (macOS) ---
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
fm.fontManager.addfont(FONT_PATH)
plt.rcParams["font.family"] = fm.FontProperties(fname=FONT_PATH).get_name()
plt.rcParams["axes.unicode_minus"] = False

# --- dataviz 스킬 팔레트 (references/palette.md) ---
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

# 국가 고정 색(카테고리 슬롯1/2, 전 그래프 공통)
COUNTRY_COLOR = {"KR": "#2a78d6", "JP": "#eb6834"}
COUNTRY_LABEL = {"KR": "한국", "JP": "일본"}

LATEST_YEAR = 2023        # 인구(고령화율·인구증감률)의 최신 연도
INFRA_YEAR = 2023          # 양국 모두 인프라(병상수·요양기관수) 데이터가 있는 최신 연도
# 2026-08-26(5): 팀/보고서 요청으로 적재 데이터 자체를 2015~2023으로 통일했으므로
# (scripts/preprocess_and_load.py 참고) 이제 LATEST_YEAR·INFRA_YEAR가 항상 같다.


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


# ============================================================
# Page 1. Overview
# ============================================================

def fig_01_kpi(con):
    aging, popchg = con.execute("""
        SELECT AVG(aging_rate), AVG(pop_change_rate)
        FROM Fact_RegionStats f JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
    """, (LATEST_YEAR,)).fetchone()
    beds, care = con.execute("""
        SELECT AVG(medical_beds_per_10k), AVG(care_facility_per_10k)
        FROM Fact_RegionStats f JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
    """, (INFRA_YEAR,)).fetchone()

    tiles = [
        (f"평균 고령화율 ({LATEST_YEAR})", f"{aging:.1f}%"),
        (f"평균 인구증감률 ({LATEST_YEAR})", f"{popchg:+.2f}%"),
        (f"평균 병상수/1만명 ({INFRA_YEAR})", f"{beds:.1f}"),
        (f"평균 요양기관수/1만명 ({INFRA_YEAR})", f"{care:.2f}"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.4), facecolor=SURFACE)
    for ax, (label, value) in zip(axes, tiles):
        ax.set_facecolor(SURFACE)
        ax.axis("off")
        ax.text(0.5, 0.62, value, ha="center", va="center",
                fontsize=24, fontweight="bold", color=INK_PRIMARY)
        ax.text(0.5, 0.18, label, ha="center", va="center",
                fontsize=9.5, color=INK_SECONDARY)
        box = FancyBboxPatch((0.03, 0.03), 0.94, 0.94,
                              boxstyle="round,pad=0,rounding_size=0.06",
                              transform=ax.transAxes, linewidth=1,
                              edgecolor=GRIDLINE, facecolor=SURFACE)
        ax.add_patch(box)
    fig.suptitle("Overview — 한·일 고령화·인프라 핵심 지표 (64개 지역 평균)",
                 fontsize=13, color=INK_PRIMARY, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(FIG_DIR / "01_overview_kpi.png", dpi=180)
    plt.close(fig)


def fig_02_aging_trend(con):
    rows = con.execute("""
        SELECT r.country, d.year, AVG(f.aging_rate)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        GROUP BY r.country, d.year ORDER BY r.country, d.year
    """).fetchall()

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    for country in ("KR", "JP"):
        years = [y for c, y, v in rows if c == country]
        vals = [v for c, y, v in rows if c == country]
        ax.plot(years, vals, color=COUNTRY_COLOR[country], linewidth=2,
                marker="o", markersize=5, markerfacecolor=COUNTRY_COLOR[country],
                markeredgecolor=SURFACE, markeredgewidth=1.2)
    style_ax(ax)
    ax.set_title("연도별 평균 고령화율 추이 (2015~2023)", fontsize=12,
                 color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.set_ylabel("고령화율(%)", fontsize=9, color=INK_SECONDARY,
                  rotation=0, ha="right", va="bottom")
    ax.yaxis.set_label_coords(-0.02, 1.04)
    country_legend(ax, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_aging_rate_trend.png", dpi=180)
    plt.close(fig)


def fig_03_aging_by_country_bar(con):
    rows = con.execute("""
        SELECT r.country, AVG(f.aging_rate)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? GROUP BY r.country
    """, (LATEST_YEAR,)).fetchall()
    countries = [c for c, v in rows]
    vals = [v for c, v in rows]

    fig, ax = plt.subplots(figsize=(4, 4), facecolor=SURFACE)
    bars = ax.bar([COUNTRY_LABEL[c] for c in countries], vals,
                  color=[COUNTRY_COLOR[c] for c in countries], width=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f}%",
                ha="center", fontsize=10, color=INK_PRIMARY)
    style_ax(ax, y_grid=True)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_title(f"국가별 평균 고령화율 ({LATEST_YEAR})", fontsize=12,
                 color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_aging_rate_by_country.png", dpi=180)
    plt.close(fig)


def fig_04_infra_density_by_country(con):
    rows = con.execute("""
        SELECT r.country, AVG(f.medical_beds_per_10k), AVG(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? GROUP BY r.country
    """, (INFRA_YEAR,)).fetchall()
    data = {c: (beds, care) for c, beds, care in rows}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), facecolor=SURFACE)
    for ax, idx, title in [(ax1, 0, "인구 1만명당 병상수"), (ax2, 1, "인구 1만명당 요양기관수")]:
        countries = list(data.keys())
        vals = [data[c][idx] for c in countries]
        bars = ax.bar([COUNTRY_LABEL[c] for c in countries], vals,
                      color=[COUNTRY_COLOR[c] for c in countries], width=0.5)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02,
                    f"{v:.1f}", ha="center", fontsize=9.5, color=INK_PRIMARY)
        style_ax(ax, y_grid=True)
        ax.set_ylim(0, max(vals) * 1.25)
        ax.set_title(title, fontsize=10.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.suptitle(f"국가별 인프라 밀도 비교 ({INFRA_YEAR}) — 병상수·요양기관수는 단위 스케일이 달라 별도 축으로 분리",
                 fontsize=11.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIG_DIR / "04_infra_density_by_country.png", dpi=180)
    plt.close(fig)


# ============================================================
# Page 2. Deep Dive
# ============================================================

def fig_05_scatter_aging_vs_infra(con):
    rows = con.execute("""
        SELECT r.country, f.aging_rate, f.medical_beds_per_10k, f.care_facility_per_10k
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
    """, (INFRA_YEAR,)).fetchall()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor=SURFACE)
    for ax, idx, title, ylabel in [
        (ax1, 2, "고령화율 × 병상수", "병상수/1만명"),
        (ax2, 3, "고령화율 × 요양기관수", "요양기관수/1만명"),
    ]:
        for country in ("KR", "JP"):
            xs = [a for c, a, b, k in rows if c == country]
            ys = [(b if idx == 2 else k) for c, a, b, k in rows if c == country]
            ax.scatter(xs, ys, s=45, color=COUNTRY_COLOR[country], alpha=0.75,
                       edgecolor=SURFACE, linewidth=0.8, zorder=3)
        style_ax(ax)
        ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
        ax.set_xlabel("고령화율(%)", fontsize=9, color=INK_SECONDARY)
        ax.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
    country_legend(ax1, loc="upper right")
    fig.suptitle(f"고령화율과 인프라 밀도의 관계 ({INFRA_YEAR}, 지역 단위 산점도)",
                 fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(FIG_DIR / "05_scatter_aging_vs_infra.png", dpi=180)
    plt.close(fig)

    # 상관계수는 SQL이 아닌 Python(pandas)에서 계산 — sql/analysis/q3.sql, q4.sql 주석 참고
    import pandas as pd
    df = pd.DataFrame(rows, columns=["country", "aging_rate", "beds", "care"])
    for country in ("KR", "JP", None):
        sub = df if country is None else df[df["country"] == country]
        label = COUNTRY_LABEL.get(country, "전체")
        r_beds = sub["aging_rate"].corr(sub["beds"])
        r_care = sub["aging_rate"].corr(sub["care"])
        print(f"  [{label}] corr(고령화율,병상수)={r_beds:.3f}  corr(고령화율,요양기관수)={r_care:.3f}")


def fig_06_region_ranking(con):
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
        ORDER BY f.aging_rate DESC
    """, (LATEST_YEAR,)).fetchall()
    top10 = rows[:10]
    bottom10 = rows[-10:]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=SURFACE)
    for ax, subset, title in [
        (ax1, list(reversed(top10)), f"고령화율 상위 10개 지역 ({LATEST_YEAR})"),
        (ax2, list(reversed(bottom10)), f"고령화율 하위 10개 지역 ({LATEST_YEAR})"),
    ]:
        labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, v in subset]
        vals = [v for c, n, v in subset]
        colors = [COUNTRY_COLOR[c] for c, n, v in subset]
        bars = ax.barh(labels, vals, color=colors, height=0.6)
        for b, v in zip(bars, vals):
            ax.text(v + 0.3, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
                    va="center", fontsize=8.5, color=INK_PRIMARY)
        style_ax(ax, y_grid=False, x_grid=True)
        ax.set_xlim(0, max(v for c, n, v in rows) * 1.15)
        ax.set_title(title, fontsize=10.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax2, loc="lower right")
    fig.suptitle("지역별 고령화율 순위 (64개 지역, 한국 17 + 일본 47)", fontsize=12.5,
                 color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(FIG_DIR / "06_region_ranking_aging.png", dpi=180)
    plt.close(fig)


def fig_07_medical_vs_care_composition(con):
    # ⚠️ 데이터 정의 자체가 다름: 한국 "장기요양기관 기관수"는 방문요양·주야간보호·
    # 노인요양시설 등 모든 장기요양 서비스 유형을 합친 값인 반면, 일본 "介護老人福祉施設数"는
    # 그중 입소시설(특별양호노인홈) 한 유형만 센 값이다. 그래서 한국 쪽 수치가 원래
    # 훨씬 크게 나오는 것은 실제 인프라 격차라기보다 정의 차이의 영향이 크다.
    # 이 캡션 없이 차트만 보면 "한국이 돌봄 비중이 높다"로 오독하기 쉬워 반드시 명시한다.
    rows = con.execute("""
        SELECT r.country, SUM(f.medical_beds_per_10k), SUM(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
        GROUP BY r.country
    """, (INFRA_YEAR,)).fetchall()

    # 국가별 2개의 도넛 차트로 나뉘어 있던 것을, 하나의 100% 누적 가로 막대 그래프로
    # 통합 — 막대 안에서 병상수/요양기관수 구성비를 색으로 구분해 가시성을 높인다.
    data = {c: (beds, care) for c, beds, care in rows}
    order = ["JP", "KR"]  # barh는 아래부터 그려지므로 이 순서면 한국이 맨 위
    labels = [COUNTRY_LABEL[c] for c in order]
    beds_pct = [100 * data[c][0] / (data[c][0] + data[c][1]) for c in order]
    care_pct = [100 * data[c][1] / (data[c][0] + data[c][1]) for c in order]
    BEDS_COLOR, CARE_COLOR = "#2a78d6", "#eda100"

    fig, ax = plt.subplots(figsize=(8, 3.4), facecolor=SURFACE)
    ax.barh(labels, beds_pct, color=BEDS_COLOR, height=0.5, label="병상수(합)")
    ax.barh(labels, care_pct, left=beds_pct, color=CARE_COLOR, height=0.5, label="요양기관수(합)")
    for i in range(len(order)):
        ax.text(beds_pct[i] / 2, i, f"{beds_pct[i]:.0f}%", ha="center", va="center",
                fontsize=10, color="white", fontweight="bold")
        # 요양기관수 비중이 작아 막대 안에 안 들어가므로 막대 오른쪽 바깥에 라벨을 둔다
        ax.text(100 + 1.5, i, f"요양기관수 {care_pct[i]:.0f}%", ha="left", va="center",
                fontsize=9.5, color=INK_SECONDARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(0, 100)
    ax.set_xlabel("구성비(%)", fontsize=9, color=INK_SECONDARY)
    ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY,
              loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2)
    ax.set_title(f"국가별 의료 vs 돌봄 인프라 구성비 ({INFRA_YEAR})", fontsize=12.5,
                 color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.text(0.02, 0.02,
             "주의: 한국 '장기요양기관수'(전체 서비스유형 합)와 일본 '개호노인복지시설수'(입소시설 1종류)는\n"
             "정의 범위가 달라 국가 간 절대량 비교가 아님 - 국가 내부 구성비만 참고할 것",
             fontsize=8, color=INK_MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.20, 1, 1))
    fig.savefig(FIG_DIR / "07_medical_vs_care_composition.png", dpi=180)
    plt.close(fig)


# ============================================================
# Page 3. Insight & Action
# ============================================================

def fig_08_infra_gap_ranking(con):
    # 기획서 3.4 DAX 그대로(64개 지역 전체를 한 줄로 세워 순위 차)를 쓰면 일본이
    # 한국보다 전반적으로 고령화율 자체가 높아서(fig02) TOP15가 전부 일본으로만
    # 채워진다(sql/analysis/q5.sql 실행 결과 참고) — 이러면 "그 나라 안에서 상대적으로
    # 인프라가 부족한 지역"이 아니라 그냥 "일본이라서" 뽑히는 것이라 실효성이 떨어진다.
    # 그래서 시각화에서는 국가별로 따로 순위를 매긴(PARTITION BY country) 버전을 써서
    # 각 나라 안에서 진짜 취약한 지역이 드러나게 한다. 전역 순위 결과는 q5.sql에 그대로 보존.
    rows = con.execute("""
        WITH latest AS (
            SELECT r.country, r.region_name_kr, f.aging_rate,
                   (f.medical_beds_per_10k + f.care_facility_per_10k) AS infra_density
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
              AND f.care_facility_per_10k IS NOT NULL
        ),
        ranked AS (
            SELECT country, region_name_kr,
                   RANK() OVER (PARTITION BY country ORDER BY aging_rate DESC) AS aging_rank,
                   RANK() OVER (PARTITION BY country ORDER BY infra_density DESC) AS infra_rank
            FROM latest
        )
        SELECT country, region_name_kr, (aging_rank - infra_rank) AS gap
        FROM ranked ORDER BY country, gap ASC
    """, (INFRA_YEAR,)).fetchall()

    # 한국 내 TOP8 / 일본 내 TOP8 두 그래프(축 스케일도 서로 달랐음)로 나뉘어 있던 것을,
    # 하나의 그래프에 국가별 TOP10씩(총 20개 지역)을 막대 색으로만 구분해 통합한다.
    kr_top = [r for r in rows if r[0] == "KR"][:10]
    jp_top = [r for r in rows if r[0] == "JP"][:10]
    combined = sorted(kr_top + jp_top, key=lambda r: r[2])  # 격차지수 오름차순(가장 시급한 지역이 먼저)
    combined = list(reversed(combined))  # barh는 아래부터 그려지므로 뒤집어야 1위가 맨 위로

    labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, g in combined]
    vals = [g for c, n, g in combined]
    colors = [COUNTRY_COLOR[c] for c, n, g in combined]

    fig, ax = plt.subplots(figsize=(8, 8.5), facecolor=SURFACE)
    bars = ax.barh(labels, vals, color=colors, height=0.65)
    xmin, xmax = min(vals), max(vals)
    for b, v in zip(bars, vals):
        ax.text(v - abs(xmin) * 0.02 if v < 0 else v + abs(xmin) * 0.02,
                b.get_y() + b.get_height() / 2, f"{v}",
                va="center", ha="right" if v < 0 else "left", fontsize=8.5, color=INK_PRIMARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(xmin * 1.2, abs(xmin) * 0.25)
    ax.set_title(f"국가 내 인프라 확충 시급 지역 TOP 10 ({INFRA_YEAR}, 국가별 인프라 격차지수)",
                 fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax, loc="upper right")
    fig.text(0.02, 0.01,
             "인프라 격차지수 = (국가 내) 고령화율 순위 - (병상수+요양기관수)순위. 더 음수일수록 그 나라 안에서 고령화 대비 인프라가 부족한 지역.\n"
             "한국은 지역 수가 17개뿐이라 TOP10에 0 이상 값도 일부 포함됨.",
             fontsize=7.5, color=INK_MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(FIG_DIR / "08_infra_gap_ranking.png", dpi=180)
    plt.close(fig)


def fig_09_simpsons_paradox_care(con):
    # 발표 보조용: fig_05 오른쪽 패널(고령화율×요양기관수)에 국가별/전체 추세선과
    # 상관계수를 직접 그려서 Simpson's paradox(부호 반전)가 그림만 봐도 보이게 만든다.
    # 원인은 PROGRESS.md 2026-08-25 / 기획서 Insight 3 참고: 한국 "장기요양기관수"는
    # 전체 서비스유형 합산, 일본 "介護老人福祉施設数"는 입소시설 1종류만 센 값이라
    # 두 나라 점들이 (고령화율, 요양기관수) 평면에서 서로 반대쪽에 뭉쳐있다.
    import numpy as np
    import pandas as pd

    rows = con.execute("""
        SELECT r.country, f.aging_rate, f.care_facility_per_10k
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? AND f.care_facility_per_10k IS NOT NULL
    """, (INFRA_YEAR,)).fetchall()
    df = pd.DataFrame(rows, columns=["country", "aging_rate", "care"])

    fig, ax = plt.subplots(figsize=(8, 6), facecolor=SURFACE)
    for country in ("KR", "JP"):
        sub = df[df["country"] == country]
        ax.scatter(sub["aging_rate"], sub["care"], s=50, color=COUNTRY_COLOR[country],
                   alpha=0.75, edgecolor=SURFACE, linewidth=0.8, zorder=3)

    line_specs = [
        ("KR", COUNTRY_COLOR["KR"], f"한국 내부 (r={df[df.country=='KR']['aging_rate'].corr(df[df.country=='KR']['care']):+.2f})"),
        ("JP", COUNTRY_COLOR["JP"], f"일본 내부 (r={df[df.country=='JP']['aging_rate'].corr(df[df.country=='JP']['care']):+.2f})"),
        (None, INK_PRIMARY, f"전체 통합 (r={df['aging_rate'].corr(df['care']):+.2f})"),
    ]
    for country, color, label in line_specs:
        sub = df if country is None else df[df["country"] == country]
        x = sub["aging_rate"].to_numpy()
        y = sub["care"].to_numpy()
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        style = dict(linewidth=2.5, zorder=4) if country else dict(linewidth=2, linestyle="--", zorder=2)
        ax.plot(xs, slope * xs + intercept, color=color, label=label, **style)

    style_ax(ax)
    ax.set_title("고령화율 × 요양기관수 — 국가 내부는 양의 상관, 통합하면 음의 상관 (Simpson's Paradox)",
                 fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.set_xlabel("고령화율(%)", fontsize=9, color=INK_SECONDARY)
    ax.set_ylabel("요양기관수/1만명", fontsize=9, color=INK_SECONDARY)
    ax.legend(frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, loc="upper left")
    fig.text(0.02, 0.01,
             "원인: 한국 '장기요양기관수'(방문요양·주야간보호 등 전체 서비스유형 합산) vs 일본 '개호노인복지시설수'(입소시설 1종류만) — 지표 정의 범위 차이.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG_DIR / "09_simpsons_paradox_care.png", dpi=180)
    plt.close(fig)


def fig_10_aging_increase_top_regions(con):
    # 발표 보조용: 기획서 Insight 1("한국 고령화 속도가 일본의 약 2배")의 근거 지역별
    # 증가폭 top15를 막대그래프로. 실제 확인 결과 64개 지역 전체를 증가폭순으로 세우면
    # 상위 15개가 전부 한국이고, 일본에서 가장 빨리 늙는 아오모리현조차 전체 16위에 그친다
    # — 국가 평균 비교(fig_02)보다 이 사실이 "2배 빠르다"를 훨씬 강하게 뒷받침한다.
    all_rows = con.execute("""
        WITH bounds AS (
            SELECT r.region_id, r.country, r.region_name_kr,
                   MAX(CASE WHEN d.year = 2015 THEN f.aging_rate END) AS y2015,
                   MAX(CASE WHEN d.year = 2023 THEN f.aging_rate END) AS y2023
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            GROUP BY r.region_id
        )
        SELECT country, region_name_kr, (y2023 - y2015) AS delta
        FROM bounds ORDER BY delta DESC
    """).fetchall()
    rows = all_rows[:15]
    # 발표 캡션용: 일본 지역 중 증가폭이 가장 큰 지역과 그 지역의 전체(64개) 순위를 동적으로 계산
    jp_rank, jp_name, jp_delta = next(
        (i + 1, n, v) for i, (c, n, v) in enumerate(all_rows) if c == "JP"
    )

    avg_kr, avg_jp = con.execute("""
        WITH bounds AS (
            SELECT r.region_id, r.country,
                   MAX(CASE WHEN d.year = 2015 THEN f.aging_rate END) AS y2015,
                   MAX(CASE WHEN d.year = 2023 THEN f.aging_rate END) AS y2023
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            GROUP BY r.region_id
        )
        SELECT AVG(CASE WHEN country='KR' THEN y2023-y2015 END),
               AVG(CASE WHEN country='JP' THEN y2023-y2015 END)
        FROM bounds
    """).fetchone()

    rows = list(reversed(rows))  # barh는 아래부터 그려지므로 1위가 맨 위로
    labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, v in rows]
    vals = [v for c, n, v in rows]
    colors = [COUNTRY_COLOR[c] for c, n, v in rows]

    fig, ax = plt.subplots(figsize=(7.5, 6), facecolor=SURFACE)
    bars = ax.barh(labels, vals, color=colors, height=0.65)
    for b, v in zip(bars, vals):
        ax.text(v + 0.08, b.get_y() + b.get_height() / 2, f"+{v:.1f}%p",
                va="center", fontsize=8.5, color=INK_PRIMARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(0, max(vals) * 1.2)
    ax.set_title("2015→2023 고령화율 증가폭 TOP15 (64개 지역 중)",
                 fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    ax.set_xlabel("증가폭(%p)", fontsize=9, color=INK_SECONDARY)
    n_years = 2023 - 2015
    fig.text(0.02, 0.01,
             f"일본 1위({jp_name}, +{jp_delta:.1f}%p)는 전체 {jp_rank}위. {n_years}년 평균 증가폭: 한국 +{avg_kr:.1f}%p(연 {avg_kr/n_years:.2f}%p) vs 일본 +{avg_jp:.1f}%p(연 {avg_jp/n_years:.2f}%p) — 한국이 약 {avg_kr/avg_jp:.1f}배.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG_DIR / "10_aging_increase_top_regions.png", dpi=180)
    plt.close(fig)


def fig_11_global_vs_country_ranking(con):
    # 발표 보조용: Insight 2("전역 순위로 보면 착시가 생긴다")의 before/after 대조.
    # 왼쪽 = 기획서 3.4 DAX 그대로(전역 랭킹, sql/analysis/q5.sql과 동일 로직) TOP10 —
    # 일본이 한국보다 고령화율 자체가 전반적으로 높아서 사실상 전부 일본으로 채워진다.
    # 오른쪽 = fig_08과 동일한 국가별(PARTITION BY country) 랭킹 TOP5씩 — 진짜 취약지역.
    global_rows = con.execute("""
        WITH latest AS (
            SELECT r.country, r.region_name_kr, f.aging_rate,
                   (f.medical_beds_per_10k + f.care_facility_per_10k) AS infra_density
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
              AND f.care_facility_per_10k IS NOT NULL
        ),
        ranked AS (
            SELECT country, region_name_kr,
                   RANK() OVER (ORDER BY aging_rate DESC) AS aging_rank,
                   RANK() OVER (ORDER BY infra_density DESC) AS infra_rank
            FROM latest
        )
        SELECT country, region_name_kr, (aging_rank - infra_rank) AS gap
        FROM ranked ORDER BY gap ASC LIMIT 10
    """, (INFRA_YEAR,)).fetchall()

    partitioned_rows = con.execute("""
        WITH latest AS (
            SELECT r.country, r.region_name_kr, f.aging_rate,
                   (f.medical_beds_per_10k + f.care_facility_per_10k) AS infra_density
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
              AND f.care_facility_per_10k IS NOT NULL
        ),
        ranked AS (
            SELECT country, region_name_kr,
                   RANK() OVER (PARTITION BY country ORDER BY aging_rate DESC) AS aging_rank,
                   RANK() OVER (PARTITION BY country ORDER BY infra_density DESC) AS infra_rank
            FROM latest
        )
        SELECT country, region_name_kr, (aging_rank - infra_rank) AS gap
        FROM ranked ORDER BY country, gap ASC
    """, (INFRA_YEAR,)).fetchall()
    mixed = ([r for r in partitioned_rows if r[0] == "KR"][:5]
             + [r for r in partitioned_rows if r[0] == "JP"][:5])
    mixed.sort(key=lambda r: r[2])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor=SURFACE)
    for ax, subset, title in [
        (ax1, list(reversed(global_rows)), "전역 랭킹 TOP10 — 기획서 DAX 그대로"),
        (ax2, list(reversed(mixed)), "국가별 랭킹 TOP5씩 — 진짜 취약지역"),
    ]:
        labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, g in subset]
        vals = [g for c, n, g in subset]
        colors = [COUNTRY_COLOR[c] for c, n, g in subset]
        bars = ax.barh(labels, vals, color=colors, height=0.6)
        xmin = min(vals)
        for b, v in zip(bars, vals):
            ax.text(v + abs(xmin) * 0.03, b.get_y() + b.get_height() / 2, f"{v}",
                    va="center", ha="left", fontsize=8.5, color=INK_PRIMARY)
        style_ax(ax, y_grid=False, x_grid=True)
        ax.set_xlim(xmin * 1.3, abs(xmin) * 0.3)
        ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.suptitle(f"인프라 격차지수, 전역 순위 vs 국가별 순위 ({INFRA_YEAR})",
                 fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.text(0.02, 0.01,
             "왼쪽은 일본이 한국보다 고령화율 자체가 높아서 생기는 착시일 뿐, 그 지역만의 진짜 인프라 부족을 보여주지 못한다 — 그래서 오른쪽처럼 국가 내 순위로 봐야 한다.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(FIG_DIR / "11_global_vs_country_ranking.png", dpi=180)
    plt.close(fig)


def main():
    con = sqlite3.connect(DB_PATH)
    fig_01_kpi(con)
    fig_02_aging_trend(con)
    fig_03_aging_by_country_bar(con)
    fig_04_infra_density_by_country(con)
    print("Q3/Q4 상관계수:")
    fig_05_scatter_aging_vs_infra(con)
    fig_06_region_ranking(con)
    fig_07_medical_vs_care_composition(con)
    fig_08_infra_gap_ranking(con)
    fig_09_simpsons_paradox_care(con)
    fig_10_aging_increase_top_regions(con)
    fig_11_global_vs_country_ranking(con)
    con.close()
    print(f"완료. {FIG_DIR}에 그래프 11장 저장됨.")


if __name__ == "__main__":
    main()
