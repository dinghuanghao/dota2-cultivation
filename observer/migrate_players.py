"""Migrate players from JSON to database."""
import json
from pathlib import Path
from .database import Database
from .config import Config

def migrate_players():
    """Migrate players from JSON to database."""
    config = Config()
    db = Database(config.DATABASE_PATH)
    
    # Read existing players
    with open(config.PLAYER_LIST_PATH) as f:
        players = json.load(f)
    
    # Add to database
    for account_id in players:
        db.add_player(int(account_id))
        print(f"Migrated player {account_id}")

if __name__ == '__main__':
    migrate_players()
