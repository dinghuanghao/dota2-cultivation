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
        
        # Check if old players table exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='players'
        """)
        old_table_exists = cursor.fetchone() is not None
        
        if old_table_exists:
            # If old table exists, run migration
            migration_path = Path(__file__).parent / '001_simplify_players.sql'
            with open(migration_path) as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)
        else:
            # If starting fresh, just create schema
            schema_path = Path(__file__).parent.parent / 'schema.sql'
            with open(schema_path) as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
        
        conn.commit()
        logger.info("Successfully initialized/migrated database")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = Path(__file__).parent.parent / 'matches.db'
    run_migrations(db_path)
