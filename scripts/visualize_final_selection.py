"""팀 최종 선정을 위해 새로 필요한 그래프 3종 (24~26).
나머지 7개(그림 7자리는 예외 — 도넛으로 교체)는 기존 파일을 그대로 재사용한다.

1. 24_indicators_combined_bar.png — 한국·일본 합친 고령화·인프라 지표 막대 (최종선정 1번)
2. 25_medical_care_donut.png      — 국가별 의료 vs 돌봄 인프라 구성비 도넛 (최종선정 6번, 그림07 도넛판)
3. 26_infra_gap_top5_combined.png — 국가별 인프라격차지수 TOP5 통합 (최종선정 9번, 그림11 오른쪽 패널 단독)
"""
import sqlite3

import matplotlib.pyplot as plt

from visualize import (
    DB_PATH, FIG_DIR, SURFACE, INK_PRIMARY, INK_SECONDARY, INK_MUTED,
    COUNTRY_COLOR, COUNTRY_LABEL, style_ax, country_legend,
)

LATEST_YEAR = 2023
INFRA_YEAR = 2023


# ============================================================
# 24. 국가별 고령화·인프라 지표 — 한일 합친 막대 (최종선정 1번)
# ============================================================

def fig_24_indicators_combined(con):
    """Power BI 재현: 묶은 세로 막대형 차트 3개(지표별 1개), 각 차트 X축=국가명.
    기존 03번(고령화율)·04번(인프라밀도, 이미 지표별 2패널)과 동일한 방식 — 이번엔
    고령화율까지 포함해 3패널로 한 화면에 모은 버전."""
    row = con.execute("""
        SELECT r.country, AVG(f.aging_rate), AVG(f.medical_beds_per_10k), AVG(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ?
        GROUP BY r.country
    """, (LATEST_YEAR,)).fetchall()
    data = {c: (aging, beds, care) for c, aging, beds, care in row}
    countries = ["KR", "JP"]

    metrics = [
        ("평균 고령화율", 0, "{:.1f}%"),
        ("인구 1만명당 병상수", 1, "{:.1f}"),
        ("인구 1만명당 요양기관수", 2, "{:.2f}"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.3), facecolor=SURFACE)
    for ax, (title, idx, fmt) in zip(axes, metrics):
        vals = [data[c][idx] for c in countries]
        bars = ax.bar([COUNTRY_LABEL[c] for c in countries], vals,
                      color=[COUNTRY_COLOR[c] for c in countries], width=0.5)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, fmt.format(v),
                    ha="center", fontsize=10.5, color=INK_PRIMARY, fontweight="bold")
        style_ax(ax, y_grid=True)
        ax.set_ylim(0, max(vals) * 1.25)
        ax.set_title(title, fontsize=10.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.suptitle(f"국가별 고령화·인프라 지표 ({LATEST_YEAR}, 한국·일본 통합 비교)", fontsize=12.5,
                 color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(FIG_DIR / "24_indicators_combined_bar.png", dpi=180)
    plt.close(fig)


# ============================================================
# 25. 국가별 의료 vs 돌봄 인프라 구성비 — 도넛 (최종선정 6번)
# ============================================================

def fig_25_medical_care_donut(con):
    """Power BI 재현: 도넛형 차트(Donut chart) 2개(한국용/일본용).
    - 범례: 지표(병상수/요양기관수), 값: SUM(medical_beds_per_10k), SUM(care_facility_per_10k)
    - Power BI 도넛은 피벗 해제(지표/값 두 열)가 필요."""
    rows = con.execute("""
        SELECT r.country, SUM(f.medical_beds_per_10k), SUM(f.care_facility_per_10k)
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = ? AND f.medical_beds_per_10k IS NOT NULL
        GROUP BY r.country
    """, (INFRA_YEAR,)).fetchall()
    data = {c: (beds, care) for c, beds, care in rows}
    BEDS_COLOR, CARE_COLOR = "#2a78d6", "#eda100"

    fig, axes = plt.subplots(1, 2, figsize=(9, 5), facecolor=SURFACE)
    for ax, country in zip(axes, ("KR", "JP")):
        beds, care = data[country]
        total = beds + care
        vals = [beds, care]
        labels = [f"병상수\n{beds/total*100:.0f}%", f"요양기관수\n{care/total*100:.0f}%"]
        wedges, texts = ax.pie(
            vals, colors=[BEDS_COLOR, CARE_COLOR], startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=SURFACE, linewidth=2),
        )
        for i, w in enumerate(wedges):
            ang = (w.theta2 + w.theta1) / 2
            import numpy as np
            x, y = np.cos(np.radians(ang)), np.sin(np.radians(ang))
            ax.text(x * 0.78, y * 0.78, labels[i], ha="center", va="center",
                    fontsize=9, color="white" if i == 0 else INK_PRIMARY, fontweight="bold")
        ax.text(0, 0, COUNTRY_LABEL[country], ha="center", va="center", fontsize=13,
                color=COUNTRY_COLOR[country], fontweight="bold")
        ax.set_title(f"{COUNTRY_LABEL[country]} ({INFRA_YEAR})", fontsize=11,
                     color=INK_PRIMARY, fontweight="bold")
    fig.suptitle("국가별 의료 vs 돌봄 인프라 구성비", fontsize=12.5, color=INK_PRIMARY,
                 x=0.02, ha="left", fontweight="bold")
    fig.text(0.02, 0.02,
             "주의: 한국 '장기요양기관수'(전체 서비스유형 합)와 일본 '개호노인복지시설수'(입소시설 1종류)는 "
             "정의 범위가 달라 국가 간 절대량 비교가 아님 — 국가 내부 구성비만 참고.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.06, 1, 0.90))
    fig.savefig(FIG_DIR / "25_medical_care_donut.png", dpi=180)
    plt.close(fig)


# ============================================================
# 26. 국가별 인프라격차지수 TOP5 통합 (최종선정 9번, 기존 11번 오른쪽 패널 단독)
# ============================================================

def fig_26_infra_gap_top5_combined(con):
    """Power BI 재현: 기존 08번(TOP10×2, 국가별)과 같은 로직인데 상위 5개씩만 뽑아
    하나의 가로 막대형 차트에 합친다(격차지수 오름차순 정렬, 국가는 막대 색으로만 구분)."""
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
    mixed = ([r for r in rows if r[0] == "KR"][:5] + [r for r in rows if r[0] == "JP"][:5])
    mixed.sort(key=lambda r: r[2])
    mixed = list(reversed(mixed))

    labels = [f"{n}({COUNTRY_LABEL[c]})" for c, n, g in mixed]
    vals = [g for c, n, g in mixed]
    colors = [COUNTRY_COLOR[c] for c, n, g in mixed]

    fig, ax = plt.subplots(figsize=(8, 5.2), facecolor=SURFACE)
    bars = ax.barh(labels, vals, color=colors, height=0.6)
    xmin = min(vals)
    for b, v in zip(bars, vals):
        ax.text(v + abs(xmin) * 0.03, b.get_y() + b.get_height() / 2, f"{v}",
                va="center", ha="left", fontsize=9, color=INK_PRIMARY)
    style_ax(ax, y_grid=False, x_grid=True)
    ax.set_xlim(xmin * 1.3, abs(xmin) * 0.3)
    ax.set_title(f"국가별 인프라 격차지수 TOP5 통합 ({INFRA_YEAR}, 한국 TOP5 + 일본 TOP5)",
                 fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax, loc="lower right")
    fig.text(0.02, 0.01,
             "인프라 격차지수 = (국가 내) 고령화율 순위 - 인프라밀도 순위. 더 음수일수록 그 나라 안에서 인프라 확충이 시급.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    fig.savefig(FIG_DIR / "26_infra_gap_top5_combined.png", dpi=180)
    plt.close(fig)


def main():
    con = sqlite3.connect(DB_PATH)
    fig_24_indicators_combined(con)
    fig_25_medical_care_donut(con)
    fig_26_infra_gap_top5_combined(con)
    con.close()
    print(f"완료. {FIG_DIR}에 그래프 3장(24~26) 저장됨.")


if __name__ == "__main__":
    main()
