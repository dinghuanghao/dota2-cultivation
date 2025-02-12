"""Script to migrate player_matches data to match_ids JSON array."""
import sqlite3
import json
import logging
from pathlib import Path
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_matches():
    """Migrate player_matches data to match_ids JSON array."""
    config = Config()
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all player-match relationships
        cursor.execute("""
            SELECT account_id, GROUP_CONCAT(match_id) as match_ids
            FROM player_matches
            GROUP BY account_id
        """)
        
        # Update players table
        for row in cursor.fetchall():
            match_ids = [int(x) for x in row['match_ids'].split(',')]
            cursor.execute("""
                UPDATE players
                SET match_ids = ?
                WHERE account_id = ?
            """, (json.dumps(match_ids), row['account_id']))
            logger.info(f"Migrated {len(match_ids)} matches for player {row['account_id']}")

        # Drop player_matches table
        cursor.execute("DROP TABLE player_matches")
        conn.commit()
        logger.info("Migration completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_matches()
