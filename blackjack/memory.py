"""SQLite memory of every card seen, by table, shoe, round, seat and hand.

The tracker writes each card once when it is confirmed. On restart the open
shoe is rebuilt from here, so cards that have left the screen still count.
"""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS shoes (
    id INTEGER PRIMARY KEY, table_id TEXT NOT NULL, started_at TEXT NOT NULL,
    ended_at TEXT, start_reason TEXT, end_reason TEXT,
    reliable INTEGER NOT NULL DEFAULT 1, unreliable_reason TEXT);
CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY, shoe_id INTEGER NOT NULL REFERENCES shoes(id),
    table_id TEXT NOT NULL, round_no INTEGER NOT NULL,
    started_at TEXT NOT NULL, ended_at TEXT);
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY, round_id INTEGER NOT NULL REFERENCES rounds(id),
    shoe_id INTEGER NOT NULL REFERENCES shoes(id), table_id TEXT NOT NULL,
    zone TEXT NOT NULL, hand_index INTEGER NOT NULL, position INTEGER NOT NULL,
    label TEXT NOT NULL, rank INTEGER NOT NULL, confidence REAL, source TEXT NOT NULL,
    x REAL, y REAL, seen_at TEXT NOT NULL, corrected_from TEXT,
    void INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, table_id TEXT NOT NULL, shoe_id INTEGER,
    at TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT);
CREATE INDEX IF NOT EXISTS cards_shoe ON cards(shoe_id, void);
CREATE INDEX IF NOT EXISTS cards_seat ON cards(table_id, zone);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Memory:
    def __init__(self, path=":memory:"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def _insert(self, sql, args):
        with self.db:
            return self.db.execute(sql, args).lastrowid

    def event(self, table_id, kind, detail=None, shoe_id=None):
        self._insert("INSERT INTO events(table_id, shoe_id, at, kind, detail) VALUES (?,?,?,?,?)",
                     (table_id, shoe_id, now(), kind, detail))

    # Shoes -----------------------------------------------------------------
    def open_shoe(self, table_id, reason, reliable=True, unreliable_reason=None):
        return self._insert(
            "INSERT INTO shoes(table_id, started_at, start_reason, reliable, unreliable_reason)"
            " VALUES (?,?,?,?,?)", (table_id, now(), reason, int(reliable), unreliable_reason))

    def close_shoe(self, shoe_id, reason):
        with self.db:
            self.db.execute("UPDATE shoes SET ended_at=?, end_reason=? WHERE id=? AND ended_at IS NULL",
                            (now(), reason, shoe_id))

    def mark_unreliable(self, shoe_id, why):
        with self.db:
            self.db.execute("UPDATE shoes SET reliable=0, unreliable_reason=COALESCE("
                            "unreliable_reason || '; ' || ?, ?) WHERE id=?", (why, why, shoe_id))

    def open_shoe_for(self, table_id):
        return self.db.execute("SELECT * FROM shoes WHERE table_id=? AND ended_at IS NULL "
                               "ORDER BY id DESC LIMIT 1", (table_id,)).fetchone()

    def shoe(self, shoe_id):
        return self.db.execute("SELECT * FROM shoes WHERE id=?", (shoe_id,)).fetchone()

    # Rounds ----------------------------------------------------------------
    def open_round(self, shoe_id, table_id):
        row = self.db.execute("SELECT COALESCE(MAX(round_no), 0) + 1 FROM rounds WHERE shoe_id=?",
                              (shoe_id,)).fetchone()
        round_no = row[0]
        round_id = self._insert("INSERT INTO rounds(shoe_id, table_id, round_no, started_at)"
                                " VALUES (?,?,?,?)", (shoe_id, table_id, round_no, now()))
        return round_id, round_no

    def close_round(self, round_id):
        with self.db:
            self.db.execute("UPDATE rounds SET ended_at=? WHERE id=? AND ended_at IS NULL",
                            (now(), round_id))

    def open_round_for(self, shoe_id):
        return self.db.execute("SELECT * FROM rounds WHERE shoe_id=? AND ended_at IS NULL "
                               "ORDER BY id DESC LIMIT 1", (shoe_id,)).fetchone()

    # Cards -----------------------------------------------------------------
    def add_card(self, round_id, shoe_id, table_id, zone, hand_index, position, card,
                 confidence, source, x=None, y=None):
        return self._insert(
            "INSERT INTO cards(round_id, shoe_id, table_id, zone, hand_index, position, label,"
            " rank, confidence, source, x, y, seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (round_id, shoe_id, table_id, zone, hand_index, position, card.label, card.rank,
             confidence, source, x, y, now()))

    def correct_card(self, card_id, card, confidence, source):
        with self.db:
            self.db.execute("UPDATE cards SET corrected_from=label, label=?, rank=?, confidence=?,"
                            " source=? WHERE id=?",
                            (card.label, card.rank, confidence, source, card_id))

    def void_card(self, card_id):
        with self.db:
            self.db.execute("UPDATE cards SET void=1 WHERE id=?", (card_id,))

    def shoe_cards(self, shoe_id):
        return self.db.execute("SELECT * FROM cards WHERE shoe_id=? AND void=0 ORDER BY id",
                               (shoe_id,)).fetchall()

    def round_cards(self, round_id):
        return self.db.execute("SELECT * FROM cards WHERE round_id=? AND void=0 "
                               "ORDER BY zone, hand_index, position", (round_id,)).fetchall()

    def seat_history(self, table_id, zone, limit=100):
        return self.db.execute("SELECT * FROM cards WHERE table_id=? AND zone=? AND void=0 "
                               "ORDER BY id DESC LIMIT ?", (table_id, zone, limit)).fetchall()

    # Observation stats (what the research said to measure) ------------------
    def shoe_summary(self, table_id, limit=50):
        """Cards dealt per finished shoe; the basis for measuring penetration."""
        return self.db.execute(
            "SELECT s.id, s.started_at, s.ended_at, s.reliable, s.end_reason,"
            " (SELECT COUNT(*) FROM cards c WHERE c.shoe_id=s.id AND c.void=0) AS cards,"
            " (SELECT COUNT(*) FROM rounds r WHERE r.shoe_id=s.id) AS rounds"
            " FROM shoes s WHERE s.table_id=? ORDER BY s.id DESC LIMIT ?",
            (table_id, limit)).fetchall()
