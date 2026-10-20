"""Power BI에서 재현할 '가시성 있는' 그래프 4종의 예시 이미지.
기존 figures/01~11(막대·선·산점도) 이외의 새 시각화 타입 제안 —
전부 실제 DB(aging_infra.db) 쿼리 결과로 그리며, 값을 지어내지 않는다.
각 함수 docstring에 Power BI 재현 레시피(시각적 개체·필드·DAX)를 적어둔다.

실행: python3 scripts/visualize_powerbi_ideas.py
"""
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

from visualize import (
    BASE, DB_PATH, FIG_DIR, SURFACE, INK_PRIMARY, INK_SECONDARY, INK_MUTED,
    GRIDLINE, BASELINE, COUNTRY_COLOR, COUNTRY_LABEL, style_ax, country_legend,
)

YEARS = list(range(2015, 2024))


def _highlight_regions(con):
    """모든 4개 차트가 공유하는 '주목 지역' 9곳: 한국 고령화 증가폭 TOP6 +
    일본 증가폭 TOP2(아오모리·아키타) + 한국 최저 고령화율(세종, 대조군)."""
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
        SELECT country, region_name_kr, y15, y23, (y23 - y15) AS delta
        FROM bounds ORDER BY delta DESC
    """).fetchall()
    kr_top6 = [r for r in rows if r[0] == "KR"][:6]
    jp_top2 = [r for r in rows if r[0] == "JP"][:2]
    sejong = next(r for r in rows if r[1] == "세종특별자치시")
    return kr_top6 + jp_top2 + [sejong]


# ============================================================
# 12. 슬로프 차트 — 2015 vs 2023 고령화율 (지역별 변화폭)
# ============================================================

def fig_12_slope_chart(con):
    """Power BI 재현: 꺾은선형 차트(Line chart).
    - 축(X축): Year — 슬라이서/필터로 2015·2023 두 값만 남긴다.
    - 범례(Legend): region_name_kr
    - 값(Y축): aging_rate
    - 데이터를 '주목 지역 9곳'으로만 필터링(그 외 64개 지역은 배경용으로만
      회색 얇은 선 전체 추가 — 같은 시각적 개체에 필터 없는 보조 선 레이어를
      만들기 어렵다면, 배경 회색 선은 생략하고 9개 강조선만 써도 무방).
    - 조건부 서식: '데이터 레이블'을 켜고 2023 지점에만 지역명+증가폭(%p) 표시.
    """
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, d.year, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year IN (2015, 2023)
        ORDER BY r.region_id, d.year
    """).fetchall()

    highlight = _highlight_regions(con)
    highlight_names = {h[1] for h in highlight}

    fig, ax = plt.subplots(figsize=(7.5, 7), facecolor=SURFACE)

    # 배경: 나머지 55개 지역은 옅은 회색 배경선(Power BI에서는 생략 가능)
    by_region = {}
    for c, n, y, v in rows:
        by_region.setdefault((c, n), {})[y] = v
    for (c, n), yv in by_region.items():
        if n in highlight_names:
            continue
        ax.plot([2015, 2023], [yv[2015], yv[2023]], color=BASELINE,
                linewidth=0.8, alpha=0.5, zorder=1)

    for c, n, y15, y23, delta in highlight:
        ax.plot([2015, 2023], [y15, y23], color=COUNTRY_COLOR[c],
                linewidth=2.4, marker="o", markersize=5,
                markerfacecolor=COUNTRY_COLOR[c], markeredgecolor=SURFACE,
                zorder=3)
        ax.text(2023 + 0.15, y23, f"{n} (+{delta:.1f}%p)", fontsize=8.5,
                va="center", color=INK_PRIMARY)

    style_ax(ax, y_grid=True)
    ax.set_xlim(2014.7, 2026.5)
    ax.set_xticks([2015, 2023])
    ax.set_xlabel("")
    ax.set_ylabel("고령화율(%)", fontsize=9, color=INK_SECONDARY,
                  rotation=0, ha="right", va="bottom")
    ax.yaxis.set_label_coords(-0.02, 1.03)
    ax.set_title("슬로프 차트 — 2015→2023 고령화율 변화 (주목 지역 9곳 강조, 나머지 55곳은 배경)",
                 fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax, loc="upper left")
    fig.text(0.02, 0.01,
             "굵은 선=한국 증가폭 TOP6 + 일본 증가폭 TOP2(아오모리·아키타) + 세종(한국 최저, 대조군). 가는 회색 선=나머지 55개 지역.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_DIR / "12_slope_aging_change.png", dpi=180)
    plt.close(fig)


# ============================================================
# 13. Small Multiples — 지역별 고령화율 추이 그리드
# ============================================================

def fig_13_small_multiples(con):
    """Power BI 재현: 꺾은선형 차트 + '소형 다중 항목(Small multiples)' 필드에
    region_name_kr을 넣는다(Power BI 코어 기능, 추가 설치 불필요).
    - 축: Year, 값: aging_rate, 소형 다중 항목: region_name_kr
    - 그리드 레이아웃(행/열 수)은 서식 창 > 소형 다중 항목에서 조정.
    - 배경색을 국가별로 통일하려면 조건부 서식(값 기반)보다는 카드 제목 색만
      국가색으로 맞추는 정도로 타협(Power BI 소형 다중은 시리즈 색만 자동 처리).
    """
    highlight = _highlight_regions(con)  # 9곳: KR 6 + JP 2 + 세종
    names = [h[1] for h in highlight]
    countries = {h[1]: h[0] for h in highlight}

    rows = con.execute(f"""
        SELECT r.region_name_kr, d.year, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE r.region_name_kr IN ({",".join("?" * len(names))})
        ORDER BY r.region_name_kr, d.year
    """, names).fetchall()

    by_region = {}
    for n, y, v in rows:
        by_region.setdefault(n, {"years": [], "vals": []})
        by_region[n]["years"].append(y)
        by_region[n]["vals"].append(v)

    fig, axes = plt.subplots(3, 3, figsize=(9, 7.5), facecolor=SURFACE, sharex=True)
    y_all = [v for n, y, v in rows]
    ymin, ymax = min(y_all) - 1, max(y_all) + 1
    for ax, n in zip(axes.flat, names):
        c = countries[n]
        d = by_region[n]
        ax.plot(d["years"], d["vals"], color=COUNTRY_COLOR[c], linewidth=2)
        ax.fill_between(d["years"], d["vals"], ymin, color=COUNTRY_COLOR[c], alpha=0.08)
        ax.set_ylim(ymin, ymax)
        ax.set_title(f"{n} ({COUNTRY_LABEL[c]})", fontsize=9.5, color=INK_PRIMARY,
                     loc="left", fontweight="bold")
        style_ax(ax, y_grid=True)
        ax.tick_params(labelsize=7.5)
        ax.set_xticks([2015, 2019, 2023])
    fig.suptitle("Small Multiples — 주목 지역 9곳 고령화율 추이 (2015~2023, 동일 Y축 스케일)",
                 fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(FIG_DIR / "13_small_multiples_trend.png", dpi=180)
    plt.close(fig)


# ============================================================
# 14. 범프 차트 — 연도별 고령화율 순위 흐름
# ============================================================

def fig_14_bump_chart(con):
    """Power BI 재현: 꺾은선형 차트 + DAX 순위 측정값.
    순위 측정값(DAX 예시):
        AgingRank =
        RANKX(
            ALL(Dim_Region),
            CALCULATE(AVERAGE(Fact_RegionStats[aging_rate])),
            , DESC
        )
    - 축: Year, 범례: region_name_kr, 값: [AgingRank] (Y축은 '값 내림차순'
      옵션으로 뒤집어 1위가 위로 오게 한다).
    - Power BI에는 네이티브 범프 차트가 없지만, 값 대신 '순위' 측정값을 선에
      꽂는 것만으로 동일한 효과를 낸다 — 커스텀 시각 개체 설치가 필요 없다.
    """
    all_rows = con.execute("""
        SELECT r.region_id, r.country, r.region_name_kr, d.year, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        ORDER BY d.year, f.aging_rate DESC
    """).fetchall()

    rank_by_year = {}
    for y in YEARS:
        yr_rows = [r for r in all_rows if r[3] == y]
        yr_rows.sort(key=lambda r: -r[4])
        for rank, (rid, c, n, yy, v) in enumerate(yr_rows, start=1):
            rank_by_year.setdefault(n, {})[y] = rank

    highlight = _highlight_regions(con)
    countries = {h[1]: h[0] for h in highlight}

    fig, ax = plt.subplots(figsize=(9.5, 7.5), facecolor=SURFACE)
    for n, c in countries.items():
        ranks = [rank_by_year[n][y] for y in YEARS]
        ax.plot(YEARS, ranks, color=COUNTRY_COLOR[c], linewidth=2.2,
                marker="o", markersize=4, markerfacecolor=COUNTRY_COLOR[c],
                markeredgecolor=SURFACE, zorder=3)

    # 라벨 겹침 방지: 최소 간격(가상 순위폭 3칸)을 강제로 벌려서 배치.
    def spaced(items, min_gap=3.0):
        # items: [(rank, name, country), ...], rank 오름차순 정렬 후 그리디로 벌림
        items = sorted(items)
        placed = []
        for rank, n, c in items:
            y = rank if not placed else max(rank, placed[-1] + min_gap)
            placed.append(y)
        return list(zip(items, placed))

    ends_2023 = spaced([(rank_by_year[n][2023], n, c) for n, c in countries.items()])
    ends_2015 = spaced([(rank_by_year[n][2015], n, c) for n, c in countries.items()])

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
    ax.set_ylabel("고령화율 순위 (64개 지역 중 1위=최고령)", fontsize=9,
                  color=INK_SECONDARY, rotation=0, ha="right", va="bottom")
    ax.yaxis.set_label_coords(-0.02, 1.03)
    ax.set_title("범프 차트 — 주목 지역 9곳의 고령화율 순위 흐름 (2015~2023, 64개 지역 중)",
                 fontsize=12, color=INK_PRIMARY, loc="left", fontweight="bold")
    country_legend(ax, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.text(0.02, 0.01,
             "한국 지역들이 해마다 순위를 끌어올리며 일본 지역 쪽으로 접근하는 모습을 보여준다 — Insight 1(한국 속도가 일본의 약 1.8배)의 시각적 근거.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.03, 0.86, 1))
    fig.savefig(FIG_DIR / "14_bump_chart_rank.png", dpi=180)
    plt.close(fig)


# ============================================================
# 15. 분해 트리(Decomposition Tree) 목업 — 고령인구 절대수 분해
# ============================================================

def fig_15_decomposition_tree(con):
    """Power BI 재현: 시각적 개체 '분해 트리(Decomposition tree)' — Power BI
    기본 내장 AI 시각화, 별도 설치 불필요.
    - 분석 대상(Analyze): SUM(elderly_pop), 설명 기준(Explain by): country,
      region_name_kr (드릴 순서).
    - '높은 값'(High value) AI 분할 버튼을 쓰면 자동으로 기여도 큰 지역부터
      펼쳐진다 — 발표 때 실시간으로 눌러가며 보여주면 효과적.
    - 이 이미지는 정적 목업이며, 실제 Power BI에서는 인터랙티브 드릴다운이다.
    """
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, f.elderly_pop
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = 2023
        ORDER BY r.country, f.elderly_pop DESC
    """).fetchall()
    kr = [r for r in rows if r[0] == "KR"]
    jp = [r for r in rows if r[0] == "JP"]
    total = sum(r[2] for r in rows)
    kr_total, jp_total = sum(r[2] for r in kr), sum(r[2] for r in jp)
    kr_top3, jp_top3 = kr[:3], jp[:3]

    def fmt(v):
        return f"{v/10000:,.0f}만명"

    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=SURFACE)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    def box(x, y, w, h, text, color=INK_PRIMARY, fc=SURFACE, ec=GRIDLINE, fontsize=9, bold=False):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08",
                            linewidth=1.2, edgecolor=ec, facecolor=fc, zorder=2)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
                color=color, fontweight="bold" if bold else "normal", zorder=3)
        return (x + w / 2, y, x + w / 2, y + h)

    def link(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color=BASELINE, linewidth=1.2, zorder=1)

    root_cx, root_top, root_bot = 0.85, 8.6 + 0.9, 8.6
    box(0.3, 8.6, 1.1, 0.9, f"전체 고령인구\n{fmt(total)}", fontsize=8.5, bold=True)

    kr_x, jp_x = 2.6, 6.6
    box(kr_x, 5.6, 1.6, 0.9, f"한국\n{fmt(kr_total)}", color=COUNTRY_COLOR["KR"],
        ec=COUNTRY_COLOR["KR"], fontsize=9, bold=True)
    box(jp_x, 5.6, 1.6, 0.9, f"일본\n{fmt(jp_total)}", color=COUNTRY_COLOR["JP"],
        ec=COUNTRY_COLOR["JP"], fontsize=9, bold=True)
    link(0.85, 8.6, kr_x + 0.8, 6.5)
    link(0.85, 8.6, jp_x + 0.8, 6.5)

    for i, (c, n, v) in enumerate(kr_top3):
        y = 3.6 - i * 1.15
        box(2.3, y, 2.2, 0.85, f"{n}\n{fmt(v)} ({v/kr_total*100:.0f}%)",
            color=INK_SECONDARY, fontsize=8)
        link(kr_x + 0.8, 5.6, 3.4, y + 0.85)

    for i, (c, n, v) in enumerate(jp_top3):
        y = 3.6 - i * 1.15
        box(6.3, y, 2.2, 0.85, f"{n}\n{fmt(v)} ({v/jp_total*100:.0f}%)",
            color=INK_SECONDARY, fontsize=8)
        link(jp_x + 0.8, 5.6, 7.4, y + 0.85)

    ax.text(3.4, 4.85, "고기여 지역 TOP3", ha="center", fontsize=8, color=INK_MUTED)
    ax.text(7.4, 4.85, "고기여 지역 TOP3", ha="center", fontsize=8, color=INK_MUTED)
    ax.set_title("분해 트리(목업) — 전체 65세이상인구를 국가→지역 순으로 분해 (2023)",
                 fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold", x=0.03)
    fig.text(0.03, 0.02,
             "실제 Power BI에서는 인터랙티브 드릴다운(AI '높은 값' 분할)로 동작 — 이 이미지는 정적 목업.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    fig.savefig(FIG_DIR / "15_decomposition_tree_mock.png", dpi=180)
    plt.close(fig)


# ============================================================
# squarify 트리맵 레이아웃 (표준 알고리즘, Bruls et al. 1999)
# ============================================================

def _squarify_layout(sizes, x, y, dx, dy):
    def layoutrow(sizes, x, y, dx, dy):
        width = sum(sizes) / dy
        rects, cy = [], y
        for s in sizes:
            h = s / width
            rects.append((x, cy, width, h))
            cy += h
        return rects

    def layoutcol(sizes, x, y, dx, dy):
        height = sum(sizes) / dx
        rects, cx = [], x
        for s in sizes:
            w = s / height
            rects.append((cx, y, w, height))
            cx += w
        return rects

    def layout(sizes, x, y, dx, dy):
        return layoutrow(sizes, x, y, dx, dy) if dx >= dy else layoutcol(sizes, x, y, dx, dy)

    def leftover(sizes, x, y, dx, dy):
        if dx >= dy:
            width = sum(sizes) / dy
            return x + width, y, dx - width, dy
        height = sum(sizes) / dx
        return x, y + height, dx, dy - height

    def worst(sizes, x, y, dx, dy):
        rects = layout(sizes, x, y, dx, dy)
        return max(max(w / h, h / w) for _, _, w, h in rects)

    def squarify(sizes, x, y, dx, dy):
        sizes = [s for s in sizes if s > 0]
        if not sizes:
            return []
        if len(sizes) == 1:
            return layout(sizes, x, y, dx, dy)
        i = 1
        while i < len(sizes) and worst(sizes[:i], x, y, dx, dy) >= worst(sizes[:i + 1], x, y, dx, dy):
            i += 1
        head, tail = sizes[:i], sizes[i:]
        lx, ly, ldx, ldy = leftover(head, x, y, dx, dy)
        return layout(head, x, y, dx, dy) + squarify(tail, lx, ly, ldx, ldy)

    total = sum(sizes)
    norm = [s * (dx * dy) / total for s in sizes]
    return squarify(norm, x, y, dx, dy)


def _heat_color(t, low="#eaf1fb", high="#1f4e96"):
    t = max(0.0, min(1.0, t))
    lo = np.array([int(low[i:i+2], 16) for i in (1, 3, 5)])
    hi = np.array([int(high[i:i+2], 16) for i in (1, 3, 5)])
    rgb = (lo + (hi - lo) * t) / 255
    return tuple(rgb)


# ============================================================
# 16. 워터폴 차트 — 한국 평균 고령화율 브릿지(2015→2023, 지역별 기여도)
# ============================================================

def fig_16_waterfall(con):
    """Power BI 재현: 폭포(Waterfall) 차트.
    - 카테고리(Category): region_name_kr (2015 시작값, 상위 6개 지역, '나머지
      11개 시도' 순으로 정렬 — Waterfall은 카테고리 축 순서를 그대로 따르므로
      정렬 열(sort by column)을 하나 만들어 이 순서를 고정한다.
    - 분석 축 시작(Breakdown 아님, 단순 Category+Value): 각 카테고리 값은
      DAX 측정값 [지역기여도] = (aging_rate 2023 - aging_rate 2015) / 17 로
      계산(한국 17개 시도 단순평균이므로 지역 하나의 변화가 전체 평균에
      기여하는 몫은 그 지역 변화량/17).
    - 첫 막대(2015 평균)와 마지막 막대(2023 평균)는 '합계로 설정'(Set as total)
      옵션을 켠다.
    """
    rows = con.execute("""
        WITH bounds AS (
            SELECT r.region_id, r.region_name_kr,
                   MAX(CASE WHEN d.year = 2015 THEN f.aging_rate END) AS y15,
                   MAX(CASE WHEN d.year = 2023 THEN f.aging_rate END) AS y23
            FROM Fact_RegionStats f
            JOIN Dim_Region r ON r.region_id = f.region_id
            JOIN Dim_Date d ON d.date_id = f.date_id
            WHERE r.country = 'KR'
            GROUP BY r.region_id
        )
        SELECT region_name_kr, y15, y23, (y23 - y15) AS delta
        FROM bounds ORDER BY delta DESC
    """).fetchall()
    n = len(rows)
    avg15 = sum(r[1] for r in rows) / n
    avg23 = sum(r[2] for r in rows) / n
    top6 = rows[:6]
    rest_contrib = sum(r[3] for r in rows[6:]) / n

    labels = ["평균\n(2015)"] + [r[0] for r in top6] + ["나머지\n11개 시도"] + ["평균\n(2023)"]
    contribs = [avg15] + [r[3] / n for r in top6] + [rest_contrib] + [avg23]
    is_total = [True] + [False] * 6 + [False] + [True]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=SURFACE)
    cursor = 0.0
    bar_w = 0.62
    for i, (label, val, tot) in enumerate(zip(labels, contribs, is_total)):
        if tot:
            bottom, height = 0, val
            color = INK_SECONDARY
            top_y = val
        else:
            bottom, height = cursor, val
            color = "#2a78d6"
            top_y = cursor + val
            cursor += val
        ax.bar(i, height, bottom=bottom, width=bar_w, color=color, zorder=3)
        ax.text(i, top_y + 0.15, f"{val:+.2f}" if not tot else f"{val:.1f}%",
                ha="center", fontsize=8.5, color=INK_PRIMARY,
                fontweight="bold" if tot else "normal")
        if 0 < i < len(labels) - 1:
            prev_top = cursor if not tot else cursor
    # 연결선(다음 막대 시작점까지 점선)
    run = 0.0
    tops = []
    for label, val, tot in zip(labels, contribs, is_total):
        if tot:
            tops.append(val)
        else:
            run += val
            tops.append(run)
    for i in range(len(labels) - 1):
        y = tops[i] if not is_total[i] else tops[i]
        ax.plot([i + bar_w / 2, i + 1 - bar_w / 2], [tops[i], tops[i]],
                color=BASELINE, linewidth=1, linestyle="--", zorder=2)

    style_ax(ax, y_grid=True)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("고령화율(%)", fontsize=9, color=INK_SECONDARY,
                  rotation=0, ha="right", va="bottom")
    ax.yaxis.set_label_coords(-0.02, 1.03)
    ax.set_title("워터폴 차트 — 한국 평균 고령화율 변화의 지역별 기여도 (2015→2023)",
                 fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.text(0.02, 0.01,
             f"막대값 = 해당 지역의 고령화율 변화 ÷ 17(한국 시도 수) = 전국 평균에 대한 기여분. 상위 6개 지역이 전체 증가분(+{avg23-avg15:.2f}%p)의 {(sum(r[3] for r in top6)/n)/(avg23-avg15)*100:.0f}%를 차지.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG_DIR / "16_waterfall_kr_bridge.png", dpi=180)
    plt.close(fig)


# ============================================================
# 17. 트리맵 — 고령인구 규모(크기) × 고령화율(색상)
# ============================================================

def fig_17_treemap(con):
    """Power BI 재현: 트리맵(Treemap) 시각적 개체.
    - 범주(Category): Dim_Region[country] → Dim_Region[region_name_kr] (계층)
    - 값(Values): SUM(elderly_pop) — 사각형 크기
    - 서식 창 > 데이터 색 > '색 채도(Color saturation)'에 AVERAGE(aging_rate)를
      넣으면 사각형 크기(인구 규모)와 색(고령화 심각도)을 동시에 표현 가능.
    - 국가 2개가 먼저 좌우로 나뉘고, 그 안에서 지역별로 다시 쪼개지는 구조가
      Power BI 트리맵의 기본 계층 동작과 동일하다.
    """
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, f.elderly_pop, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year = 2023
        ORDER BY r.country, f.elderly_pop DESC
    """).fetchall()
    kr = [r for r in rows if r[0] == "KR"]
    jp = [r for r in rows if r[0] == "JP"]
    kr_total = sum(r[2] for r in kr)
    jp_total = sum(r[2] for r in jp)
    grand = kr_total + jp_total

    all_aging = [r[3] for r in rows]
    amin, amax = min(all_aging), max(all_aging)

    W, H = 12.0, 7.0
    kr_w = W * kr_total / grand
    jp_w = W - kr_w

    fig, ax = plt.subplots(figsize=(12, 7.2), facecolor=SURFACE)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    for group, x0, w, label in [(kr, 0, kr_w, "한국"), (jp, kr_w, jp_w, "일본")]:
        sizes = [r[2] for r in group]
        rects = _squarify_layout(sizes, x0, 0, w, H)
        for (rx, ry, rw, rh), (c, n, pop, aging) in zip(rects, group):
            t = (aging - amin) / (amax - amin)
            fc = _heat_color(t)
            ax.add_patch(Rectangle((rx, ry), rw, rh, facecolor=fc,
                                    edgecolor=SURFACE, linewidth=1.2, zorder=2))
            if rw > 0.45 and rh > 0.35:
                fs = min(9, max(5.5, rw * 2.2))
                txt_color = "white" if t > 0.55 else INK_PRIMARY
                label_txt = n if rw > 0.9 else n[:2]
                ax.text(rx + rw / 2, ry + rh / 2, f"{label_txt}\n{aging:.0f}%",
                        ha="center", va="center", fontsize=fs, color=txt_color, zorder=3)
        ax.text(x0 + w / 2, H + 0.15, f"{label} (고령인구 {sum(r[2] for r in group)/10000:,.0f}만명)",
                ha="center", fontsize=11, color=INK_PRIMARY, fontweight="bold")

    ax.set_title("트리맵 — 지역별 고령인구 규모(면적) × 고령화율(색 진하기), 2023",
                 fontsize=12.5, color=INK_PRIMARY, loc="left", fontweight="bold", y=1.06)
    fig.text(0.02, 0.01,
             f"사각형 면적 = 65세이상인구 절대수, 색 진하기 = 고령화율({amin:.0f}~{amax:.0f}%). 좌우 폭 비율은 한국:일본 고령인구 비율({kr_total/grand*100:.0f}:{jp_total/grand*100:.0f}) 그대로.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(FIG_DIR / "17_treemap_elderly_pop.png", dpi=180)
    plt.close(fig)


# ============================================================
# 18. 히트맵 매트릭스 — 64개 지역 × 9개년 고령화율
# ============================================================

def fig_18_heatmap_matrix(con):
    """Power BI 재현: 매트릭스(Matrix) 시각적 개체.
    - 행(Rows): Dim_Region[country] → Dim_Region[region_name_kr]
    - 열(Columns): Dim_Date[year]
    - 값(Values): AVERAGE(aging_rate)
    - 서식 창 > 셀 요소(Cell elements) > '배경색'에서 규칙 기반 서식(그라디언트)
      켜기 — 최소값~최대값 색을 지정하면 이 이미지와 동일한 히트맵이 된다.
    - 64행은 매트릭스 스크롤로 전부 보여줄 수 있고, 정렬은 최신연도 열
      클릭으로 내림차순 고정 가능.
    """
    rows = con.execute("""
        SELECT r.country, r.region_name_kr, d.year, f.aging_rate
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        ORDER BY r.country, r.region_name_kr, d.year
    """).fetchall()
    by_region = {}
    order_key = {}
    for c, n, y, v in rows:
        by_region.setdefault((c, n), {})[y] = v
        if y == 2023:
            order_key[(c, n)] = v
    regions = sorted(by_region.keys(), key=lambda k: -order_key[k])
    years = YEARS
    grid = np.array([[by_region[r][y] for y in years] for r in regions])

    fig, ax = plt.subplots(figsize=(8, 13), facecolor=SURFACE)
    im = ax.imshow(grid, aspect="auto", cmap="Blues", vmin=grid.min(), vmax=grid.max())
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, fontsize=7.5, rotation=45)
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels([f"{n}({COUNTRY_LABEL[c]})" for c, n in regions], fontsize=6.3)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=7.5)
    cbar.set_label("고령화율(%)", fontsize=8, color=INK_SECONDARY)
    ax.set_title("히트맵 매트릭스 — 64개 지역 × 연도별 고령화율\n(2023년 기준 내림차순 정렬)",
                 fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 0.98, 1))
    fig.savefig(FIG_DIR / "18_heatmap_matrix.png", dpi=170)
    plt.close(fig)


# ============================================================
# 19. 재생축 산점도 필름스트립 — 연도별 고령화율×인프라밀도 변화
# ============================================================

def fig_19_play_axis_scatter(con):
    """Power BI 재현: 분산형(Scatter) 차트 + '재생 축(Play axis)' 필드.
    - X축: aging_rate, Y축: (medical_beds_per_10k + care_facility_per_10k),
      범례: country, 크기(Size): total_pop, 재생 축: Dim_Date[year].
    - 재생 축에 연도를 넣으면 ▶ 버튼으로 2015→2023 애니메이션이 자동 재생된다
      (Power BI 기본 기능, 추가 설치 불필요). 이 이미지는 애니메이션을 정지
      이미지 3장(2015·2019·2023)으로 나눈 필름스트립이다.
    """
    rows = con.execute("""
        SELECT r.country, d.year, f.aging_rate,
               (f.medical_beds_per_10k + f.care_facility_per_10k) AS infra,
               f.total_pop
        FROM Fact_RegionStats f
        JOIN Dim_Region r ON r.region_id = f.region_id
        JOIN Dim_Date d ON d.date_id = f.date_id
        WHERE d.year IN (2015, 2019, 2023)
    """).fetchall()
    xs_all = [r[2] for r in rows]
    ys_all = [r[3] for r in rows]
    pops = [r[4] for r in rows]
    xlim = (min(xs_all) - 2, max(xs_all) + 2)
    ylim = (min(ys_all) - 5, max(ys_all) + 15)
    size_scale = 900 / max(pops)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), facecolor=SURFACE, sharey=True)
    for ax, year in zip(axes, (2015, 2019, 2023)):
        for country in ("KR", "JP"):
            sub = [r for r in rows if r[1] == year and r[0] == country]
            xs = [r[2] for r in sub]
            ys = [r[3] for r in sub]
            sizes = [max(15, r[4] * size_scale) for r in sub]
            ax.scatter(xs, ys, s=sizes, color=COUNTRY_COLOR[country], alpha=0.55,
                       edgecolor=SURFACE, linewidth=0.8, zorder=3)
        style_ax(ax)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_title(f"{year}년", fontsize=11.5, color=INK_PRIMARY, loc="left", fontweight="bold")
        ax.set_xlabel("고령화율(%)", fontsize=8.5, color=INK_SECONDARY)
    axes[0].set_ylabel("인프라밀도(병상+요양기관/1만명)", fontsize=8.5, color=INK_SECONDARY)
    country_legend(axes[2], loc="upper right")
    fig.suptitle("재생축 산점도 필름스트립 — 고령화율×인프라밀도의 시간에 따른 이동 (거품 크기=총인구)",
                 fontsize=12.5, color=INK_PRIMARY, x=0.02, ha="left", fontweight="bold")
    fig.text(0.02, 0.01,
             "Power BI에서는 재생 축(Play axis)에 연도를 넣으면 이 3장이 매끄러운 애니메이션 1개로 자동 재생된다.",
             fontsize=7.5, color=INK_MUTED, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    fig.savefig(FIG_DIR / "19_play_axis_scatter_filmstrip.png", dpi=180)
    plt.close(fig)


def main():
    con = sqlite3.connect(DB_PATH)
    fig_12_slope_chart(con)
    fig_13_small_multiples(con)
    fig_14_bump_chart(con)
    fig_15_decomposition_tree(con)
    fig_16_waterfall(con)
    fig_17_treemap(con)
    fig_18_heatmap_matrix(con)
    fig_19_play_axis_scatter(con)
    con.close()
    print(f"완료. {FIG_DIR}에 그래프 8장(12~19) 저장됨.")


if __name__ == "__main__":
    main()
