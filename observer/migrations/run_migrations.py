"""Run database migrations."""
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_migrations(db_path: Path):
    """Run all migrations in order."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Run 001_simplify_players.sql
        migration_path = Path(__file__).parent / '001_simplify_players.sql'
        with open(migration_path) as f:
            migration_sql = f.read()
            conn.executescript(migration_sql)
            conn.commit()
            
        logger.info("Successfully ran migration: 001_simplify_players.sql")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = Path(__file__).parent.parent / 'matches.db'
    run_migrations(db_path)
