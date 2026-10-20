"""sql/analysis/q*.sql을 실제로 실행해서 에러 없이 결과가 나오는지 확인하고,
결과 상위 5행을 각 파일 맨 아래에 주석으로 붙인다 (CLAUDE.md 6장 규칙).
"""
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "aging_infra.db"
ANALYSIS_DIR = BASE / "sql" / "analysis"


def main():
    con = sqlite3.connect(DB_PATH)
    for path in sorted(ANALYSIS_DIR.glob("q*.sql")):
        sql = path.read_text()
        # 이전 실행 결과 주석이 파일에 이미 붙어있으면 제거하고 재실행
        sql = sql.split("\n-- === 실행 결과")[0].rstrip() + "\n"

        cur = con.execute(sql)
        headers = [d[0] for d in cur.description]
        rows = cur.fetchmany(5)

        lines = ["\n-- === 실행 결과 (상위 5행, 재실행 시 갱신됨) ==="]
        lines.append("-- " + " | ".join(headers))
        for row in rows:
            lines.append("-- " + " | ".join(str(v) for v in row))

        path.write_text(sql + "\n".join(lines) + "\n")
        print(f"[{path.name}] 실행 성공, {len(rows)}행 미리보기 저장")

    con.close()


if __name__ == "__main__":
    main()
