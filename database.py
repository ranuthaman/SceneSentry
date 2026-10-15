
import sqlite3


DB_PATH = "scenesentry.db"


def init_db(db_path=DB_PATH):
    """Create the events table if it does not exist."""

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                camera_id TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                evidence_path TEXT DEFAULT '',
                review_status TEXT DEFAULT 'needs_review'
            )
        """)


def insert_event(event, db_path=DB_PATH):
    """Save one event dictionary to the database."""

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute("""
            INSERT INTO events (
                timestamp, camera_id, category,
                summary, evidence_path, review_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event["timestamp"],
            event["camera_id"],
            event["category"],
            event["summary"],
            event.get("evidence_path", ""),
            event.get("review_status", "needs_review")
        ))

        return cursor.lastrowid


def get_events(
    camera_id=None,
    category=None,
    start_time=None,
    end_time=None,
    db_path=DB_PATH
):
    """Retrieve events with optional filters."""

    query = "SELECT * FROM events WHERE 1=1"
    parameters = []

    if camera_id:
        query += " AND camera_id = ?"
        parameters.append(camera_id)

    if category:
        query += " AND category = ?"
        parameters.append(category)

    if start_time is not None:
        query += " AND timestamp >= ?"
        parameters.append(start_time)

    if end_time is not None:
        query += " AND timestamp <= ?"
        parameters.append(end_time)

    query += " ORDER BY timestamp DESC"

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]


def get_categories(db_path=DB_PATH):
    """Return all distinct event categories."""

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT DISTINCT category FROM events ORDER BY category"
        ).fetchall()

        return [row[0] for row in rows]
