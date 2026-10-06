import sqlite3, time

DB = "learner.db"
INTERVALS = [0, 1, 3, 7, 14]   # days until next review, by box number


def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS mistakes(
        user TEXT, tag TEXT, errors INT DEFAULT 0, box INT DEFAULT 0,
        next_review REAL, PRIMARY KEY(user, tag))""")
    return c


def record(user: str, tag: str, correct: bool):
    c = conn()
    c.execute("INSERT OR IGNORE INTO mistakes(user, tag, next_review) VALUES(?,?,?)",
              (user, tag, time.time()))
    row = c.execute("SELECT box FROM mistakes WHERE user=? AND tag=?", (user, tag)).fetchone()
    box = min(row[0] + 1, len(INTERVALS) - 1) if correct else 0
    nxt = time.time() + INTERVALS[box] * 86400
    c.execute("""UPDATE mistakes SET box=?, next_review=?, errors=errors+?
                 WHERE user=? AND tag=?""", (box, nxt, 0 if correct else 1, user, tag))
    c.commit()


def due(user: str):
    return [r[0] for r in conn().execute(
        "SELECT tag FROM mistakes WHERE user=? AND next_review<=?", (user, time.time()))]


def mistake_map(user: str):
    return conn().execute(
        "SELECT tag, errors, box FROM mistakes WHERE user=? ORDER BY errors DESC", (user,)).fetchall()