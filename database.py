import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            abstract TEXT NOT NULL DEFAULT '',
            published TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            venue TEXT NOT NULL DEFAULT '',
            publisher TEXT NOT NULL DEFAULT '',
            paper_type TEXT NOT NULL DEFAULT '',
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON papers(title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON papers(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_venue ON papers(venue)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_publisher ON papers(publisher)")

    # 기존 테이블에 새 컬럼 추가 (이미 있으면 무시)
    for col, default in [("venue", "''"), ("publisher", "''"), ("paper_type", "''")]:
        try:
            conn.execute(f"ALTER TABLE papers ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        except sqlite3.OperationalError:
            pass  # 이미 존재

    conn.commit()
    conn.close()


def insert_paper(source_id: str, title: str, authors: str, abstract: str,
                 published: str, url: str, source: str = "",
                 venue: str = "", publisher: str = "", paper_type: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO papers (source_id, title, authors, abstract, published, url, source, venue, publisher, paper_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source_id, title, authors, abstract, published, url, source, venue, publisher, paper_type),
        )
        conn.commit()
    finally:
        conn.close()


def get_random_paper():
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM papers WHERE abstract != '' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_random_paper_without_summary():
    """요약이 없고 초록이 있는 논문 우선 반환"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM papers WHERE summary IS NULL AND abstract != '' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM papers WHERE abstract != '' ORDER BY RANDOM() LIMIT 1"
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_random_paper_by_venue(venue: str):
    """특정 학회/저널의 무작위 논문"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM papers WHERE venue = ? AND abstract != '' ORDER BY RANDOM() LIMIT 1",
            (venue,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_random_paper_by_publisher(publisher: str):
    """특정 퍼블리셔의 무작위 논문"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM papers WHERE publisher = ? AND abstract != '' ORDER BY RANDOM() LIMIT 1",
            (publisher,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_summary(paper_id: int, summary: str):
    conn = get_connection()
    try:
        conn.execute("UPDATE papers SET summary = ? WHERE id = ?", (summary, paper_id))
        conn.commit()
    finally:
        conn.close()


def update_abstract(paper_id: int, abstract: str):
    conn = get_connection()
    try:
        conn.execute("UPDATE papers SET abstract = ? WHERE id = ?", (abstract, paper_id))
        conn.commit()
    finally:
        conn.close()


def get_papers_without_abstract(limit: int = 50):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM papers WHERE abstract = '' LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_papers(keyword: str, limit: int = 5):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM papers WHERE title LIKE ? OR abstract LIKE ? ORDER BY published DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_paper_count():
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    finally:
        conn.close()


def get_stats():
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        with_abstract = conn.execute("SELECT COUNT(*) FROM papers WHERE abstract != ''").fetchone()[0]
        with_summary = conn.execute("SELECT COUNT(*) FROM papers WHERE summary IS NOT NULL").fetchone()[0]
        by_source = conn.execute("SELECT source, COUNT(*) as cnt FROM papers GROUP BY source").fetchall()
        by_venue = conn.execute(
            "SELECT venue, COUNT(*) as cnt FROM papers WHERE venue != '' GROUP BY venue ORDER BY cnt DESC"
        ).fetchall()
        by_publisher = conn.execute(
            "SELECT publisher, COUNT(*) as cnt FROM papers WHERE publisher != '' GROUP BY publisher ORDER BY cnt DESC"
        ).fetchall()
        return {
            "total": total,
            "with_abstract": with_abstract,
            "with_summary": with_summary,
            "by_source": {r["source"]: r["cnt"] for r in by_source},
            "by_venue": {r["venue"]: r["cnt"] for r in by_venue},
            "by_publisher": {r["publisher"]: r["cnt"] for r in by_publisher},
        }
    finally:
        conn.close()


def get_venues():
    """DB에 있는 학회/저널 목록과 논문 수"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT venue, publisher, paper_type, COUNT(*) as cnt FROM papers WHERE venue != '' GROUP BY venue ORDER BY cnt DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_summaries():
    """모든 요약 캐시 삭제 (논문 데이터는 유지)"""
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM papers WHERE summary IS NOT NULL").fetchone()[0]
        conn.execute("UPDATE papers SET summary = NULL")
        conn.commit()
        return count
    finally:
        conn.close()


def reset_db():
    """DB 전체 초기화"""
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        conn.execute("DELETE FROM papers")
        conn.commit()
        return count
    finally:
        conn.close()
