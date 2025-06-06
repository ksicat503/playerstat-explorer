"""
db.py

Handles all database operations for the PokerLens opponent modeling engine.

This module sets up and interacts with a local SQLite database to store:
- `players`: unique player names
- `player_stats`: per-player hand statistics (VPIP, PFR, 3-bet, etc.)
- `processed_hands`: which hands have been parsed

Provides helper functions to insert and aggregate stats.
"""

import sqlite3
import os

DB_NAME = "poker_model.db"

DB_PATH = "poker_model.db"
if not os.path.exists(DB_PATH):
    DB_PATH = "example_data/example_poker_model.db"


def connect():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)


def create_tables():
    """Create the necessary database tables if they don't exist."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        position TEXT,
        vpip_count INTEGER,
        pfr_count INTEGER,
        hands_played INTEGER,
        three_bet_count INTEGER,
        fold_to_four_bet_count INTEGER,
        total_four_bet_opportunities INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_hands (
        hand_id TEXT PRIMARY KEY
    )''')

    conn.commit()
    conn.close()


def hand_already_processed(hand_id):
    """Return True if hand_id is already recorded in processed_hands."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM processed_hands WHERE hand_id = ?", (hand_id,)
        )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def add_hand_id(hand_id):
    """Mark a hand as processed by inserting its ID."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO processed_hands (hand_id) VALUES (?)",
        (hand_id,)
        )
    conn.commit()
    conn.close()


def add_or_update_player(name):
    """Ensure a player exists; return their ID."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    conn.commit()
    cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
    player_id = cursor.fetchone()[0]
    conn.close()
    return player_id


def update_player_stats(
    player_id,
    position,
    vpip_count,
    pfr_count,
    hands_played,
    three_bet_count,
    fold_to_four_bet_count=0,
    total_four_bet_opportunities=0
):
    """Insert stats for one hand into player_stats."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO player_stats (
            player_id,
            position,
            vpip_count,
            pfr_count,
            hands_played,
            three_bet_count,
            fold_to_four_bet_count,
            total_four_bet_opportunities
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_id,
            position,
            vpip_count,
            pfr_count,
            hands_played,
            three_bet_count,
            fold_to_four_bet_count,
            total_four_bet_opportunities
        )
    )
    conn.commit()
    conn.close()


def get_all_player_names():
    """Return an alphabetically sorted list of all player names."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM players ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_player_overall_stats(name):
    """Fetch total hands and preflop percentages for a player."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    pid = row[0]
    cursor.execute(
        '''
        SELECT
          SUM(hands_played),
          SUM(vpip_count),
          SUM(pfr_count),
          SUM(three_bet_count)
        FROM player_stats
        WHERE player_id = ?
        ''', (pid,)
    )
    hands, vpip, pfr, three = cursor.fetchone()
    conn.close()
    if not hands:
        return {"hands": 0, "vpip_pct": 0, "pfr_pct": 0, "three_bet_pct": 0}
    return {
        "hands": hands,
        "vpip_pct": round(vpip / hands * 100, 1),
        "pfr_pct":  round(pfr / hands * 100, 1),
        "three_bet_pct": round(three / hands * 100, 1)
    }


def get_player_stats_by_position(name):
    """Fetch per position aggregate stats for a player."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    pid = row[0]
    cursor.execute(
        '''
        SELECT position,
               SUM(hands_played),
               SUM(vpip_count),
               SUM(pfr_count),
               SUM(three_bet_count)
        FROM player_stats
        WHERE player_id = ?
        GROUP BY position
        ''', (pid,)
    )
    data = {}
    for pos, h, vp, pf, tb in cursor.fetchall():
        data[pos] = {
            "hands": h,
            "vpip_pct": round(vp / h * 100, 1) if h else 0,
            "pfr_pct":  round(pf / h * 100, 1) if h else 0,
            "three_bet_pct": round(tb / h * 100, 1) if h else 0
        }
    conn.close()
    return data


def get_population_stats():
    """Compute overall population averages for VPIP, PFR, and 3-bet."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT
          SUM(hands_played),
          SUM(vpip_count),
          SUM(pfr_count),
          SUM(three_bet_count)
        FROM player_stats
        '''
    )
    row = cursor.fetchone()
    conn.close()
    if not row or row[0] is None:
        return {"vpip_pct": 0, "pfr_pct": 0, "three_bet_pct": 0}
    hands, vpip, pfr, three = row
    return {
        "vpip_pct": round(vpip / hands * 100, 1) if hands else 0,
        "pfr_pct":  round(pfr / hands * 100, 1) if hands else 0,
        "three_bet_pct": round(three / hands * 100, 1) if hands else 0
    }


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
