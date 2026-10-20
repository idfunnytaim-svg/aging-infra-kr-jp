"""팀원 피드백(2026-08-27 2차) 반영 그래프 4종.
피드백 원문 4건:
 1. 연도별 인프라 밀도 — 막대그래프 말고 다른 그래프로
 2. 한국/일본 나눠서 고령화·인프라 지표를 막대그래프(다른 것도 괜찮음)로
 3. 지역별 고령화율 상위 — 10개 지역으로 통일
 4. 고령화율 증가폭 — 한국/일본 따로따로 5개씩, 하나 더 출력

기존 01~19와 번호가 안 겹치게 20~23으로 저장한다. 전부 실제 DB 쿼리 결과.
"""
import sqlite3

import matplotlib.pyplot as plt

from visualize import (
    DB_PATH, FIG_DIR, SURFACE, INK_PRIMARY, INK_SECONDARY, INK_MUTED,
    BASELINE, COUNTRY_COLOR, COUNTRY_LABEL, style_ax, country_legend,
)

LATEST_YEAR = 2023


# ============================================================
# 20. 연도별 인프라밀도 추이 (선차트) — 피드백 1
# ============================================================

def fig_20_infra_density_trend(con):
    """Power BI 재현: 꺾은선형 차트 (fig_02와 동일한 방식, 지표만 다름).
    - X축: year (필터 없음, 2015~2023 전체)
    - 범례: 국가명
    - 값: medical_beds_per_10k → 평균 (왼쪽 차트), care_facility_per_10k → 평균 (오른쪽 차트)
    - 04번(국가별 인프라 밀도, 막대·2023년 단일시점)을 대체/보완 — 시간 흐름을 보여주려면
      막대보다 선이 적합하다는 피드백 반영.
    """
    rows = con.execute("""
        SELECT r.country, d.year, AVG(f.medical_beds_per_10k), AVG(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        GROUP BY r.country, d.year ORDER BY r.country, d.year
    """).fetchall()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=SURFACE)
    for ax, idx, title, ylabel in [
        (ax1, 2, "인구 1만명당 병상수 추이", "병상수/1만명"),
        (ax2, 3, "인구 1만명당 요양기관수 추이", "요양기관수/1만명"),
    ]:
        for country in ("KR", "JP"):
            years = [y for c, y, b, k in rows if c == country]
            vals = [(b if idx == 2 else k) for c, y, b, k in rows if c == country]
            ax.plot(years, vals, color=COUNTRY_COLOR[country], linewidth=2,
                    marker="o", markersize=4.5, markerfacecolor=COUNTRY_COLOR[country],
                    markeredgecolor=SURFACE, markeredgewidth=1)
        style_ax(ax)
        ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
    country_legend(ax1, loc="lower right")
    fig.suptitle("연도별 인프라밀도 추이 (2015~2023) — 04번(막대) 대체", fontsize=12.5,
                 color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIG_DIR / "20_infra_density_trend.png", dpi=180)
    plt.close(fig)


# ============================================================
# 21. 국가별 지표 카드형 막대 (2x3) — 피드백 2
# ============================================================

def fig_21_indicators_by_country(con):
    """Power BI 재현: 카드(Card) 6개를 2행(한국/일본) × 3열(고령화율·병상수·요양기관수)로
    배치하거나, 막대형 차트를 쓰고 싶으면 국가별로 차트 3개(지표별)를 따로 만들고
    X축에 국가명 하나만 두는 식으로 6개 미니 차트를 구성해도 동일한 효과.
    - 값: aging_rate/medical_beds_per_10k/care_facility_per_10k → 평균, year=2023 필터
    - 지표 3개는 단위(％·개수·개수) 스케일이 완전히 달라 한 막대에 같이 그리면 왜곡되므로
      지표별로 축을 분리(=카드 또는 별도 차트)하는 것을 권장.
    """
    row = con.execute("""
        SELECT r.country, AVG(f.aging_rate), AVG(f.medical_beds_per_10k), AVG(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
        GROUP BY r.country
    """, (LATEST_YEAR,)).fetchall()
    data = {c: (aging, beds, care) for c, aging, beds, care in row}

    metrics = [("고령화율(%)", 0, "{:.1f}%"), ("병상수/1만명", 1, "{:.1f}"), ("요양기관수/1만명", 2, "{:.2f}")]
    countries = ["KR", "JP"]

    fig, axes = plt.subplots(2, 3, figsize=(9, 5.5), facecolor=SURFACE)
    for row_i, country in enumerate(countries):
        for col_i, (label, idx, fmt) in enumerate(metrics):
            ax = axes[row_i, col_i]
            val = data[country][idx]
            ax.bar([0], [val], color=COUNTRY_COLOR[country], width=0.5)
            ax.text(0, val * 1.03, fmt.format(val), ha="center", fontsize=11,
                    color=INK_PRIMARY, fontweight="bold")
            ax.set_xlim(-1, 1)
            ax.set_ylim(0, val * 1.35)
            ax.set_xticks([])
            style_ax(ax, y_grid=False)
            if row_i == 0:
                ax.set_title(label, fontsize=10, color=INK_PRIMARY, fontweight="bold")
            if col_i == 0:
                ax.set_ylabel(COUNTRY_LABEL[country], fontsize=10.5, color=COUNTRY_COLOR[country],
                              fontweight="bold", rotation=90, labelpad=8)
    fig.suptitle(f"국가별 고령화·인프라 지표 ({LATEST_YEAR}, 한국/일본 행으로 분리)", fontsize=12.5,
                 color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIG_DIR / "21_indicators_by_country.png", dpi=180)
    plt.close(fig)


# ============================================================
# 22. 지역별 고령화율 TOP10 (단일 패널) — 피드백 3
# ============================================================

def fig_22_region_top10_only(con):
    """Power BI 재현: 06번과 동일하지만 '상위 N' 필터만 10으로 두고 '하위 N' 차트는
    빼서 하나로 통일.
    - 가로 막대형 차트, Y축: region_name_kr, 값: aging_rate, 범례: 국가명
    - 필터: year=2023, aging_rate 상위 10(Top N)
    """
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
        ORDER BY f.aging_rate DESC LIMIT 10
    """, (LATEST_YEAR,)).fetchall()
    rows = list(reversed(rows))

    labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, v in rows]
    vals = [v for c, n, v in rows]
    colors = [COUNTRY_COLOR[c] for c, n, v in rows]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
    bars = ax.barh(labels, vals, color=colors, height=0.6)
    for b, v in zip(bars, vals):
        ax.text(v + 0.4, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
                va="center", fontsize=9, color=INK_PRIMARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(0, max(vals) * 1.15)
    ax.set_title(f"지역별 고령화율 TOP 10 ({LATEST_YEAR}, 64개 지역 중)", fontsize=12.5,
                 color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "22_region_top10_aging.png", dpi=180)
    plt.close(fig)


# ============================================================
# 23. 고령화율 증가폭 — 한국 TOP5 / 일본 TOP5 (피드백 4)
# ============================================================

def fig_23_increase_top5_by_country(con):
    """Power BI 재현: 가로 막대형 차트 2개(한국용/일본용) — 10번(TOP15 통합, 한국이
    싹쓸이)을 보완해 일본 지역도 눈에 보이게 국가별로 각각 TOP5.
    - 계산 열/측정값: PowerBI_가이드.md 4-2의 `증가폭_2015_2023` 그대로 재사용
    - 값: 증가폭_2015_2023, 필터: country=KR(또는 JP) + 상위 N=5
    """
    rows = con.execute("""
        WITH bounds AS (
            SELECT r.region_id, r.country, r.region_name_kr,
                   MAX(CASE WHEN d.year = 2015 THEN f.aging_rate END) AS y15,
                   MAX(CASE WHEN d.year = 2023 THEN f.aging_rate END) AS y23
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            GROUP BY r.region_id
        )
        SELECT country, region_name_kr, (y23 - y15) AS delta
        FROM bounds ORDER BY country, delta DESC
    """).fetchall()
    kr_top5 = [r for r in rows if r[0] == "KR"][:5]
    jp_top5 = [r for r in rows if r[0] == "JP"][:5]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE)
    for ax, subset, country, title in [
        (ax1, kr_top5, "KR", "한국 TOP5"), (ax2, jp_top5, "JP", "일본 TOP5"),
    ]:
        subset = list(reversed(subset))
        labels = [n for c, n, v in subset]
        vals = [v for c, n, v in subset]
        bars = ax.barh(labels, vals, color=COUNTRY_COLOR[country], height=0.55)
        for b, v in zip(bars, vals):
            ax.text(v + 0.08, b.get_y() + b.get_height() / 2, f"+{v:.1f}%p",
                    va="center", fontsize=9, color=INK_PRIMARY)
        style_ax(ax, y_grid=False, x_grid=True)
        ax.set_xlim(0, max(vals) * 1.3)
        ax.set_title(title, fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.suptitle("2015→2023 고령화율 증가폭 — 국가별 TOP5 (10번 보완, 일본도 보이게 분리)",
                 fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIG_DIR / "23_increase_top5_by_country.png", dpi=180)
    plt.close(fig)


def main():
    con = sqlite3.connect(DB_PATH)
    fig_20_infra_density_trend(con)
    fig_21_indicators_by_country(con)
    fig_22_region_top10_only(con)
    fig_23_increase_top5_by_country(con)
    con.close()
    print(f"완료. {FIG_DIR}에 그래프 4장(20~23) 저장됨.")


if __name__ == "__main__":
    main()
