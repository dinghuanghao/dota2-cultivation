"""Migrate players from JSON to database."""
import json
import asyncio
from pathlib import Path
from .database import Database
from .config import Config
from .api import DotaAPI

async def migrate_players():
    """Migrate players from JSON to database."""
    config = Config()
    db = Database(config.DATABASE_PATH)
    api = DotaAPI(config.OPENDOTA_BASE_URL, config.MATCH_DETAILS_URL)
    
    try:
        # Initialize API session
        await api.init()
        
        # Read existing players
        with open(config.PLAYER_LIST_PATH) as f:
            players = json.load(f)
        
        # Add to database
        for account_id in players:
            account_id = int(account_id)
            try:
                player_info = await api.get_player_info(account_id)
                db.add_player(account_id, player_info)
                print(
                    f"Migrated player {account_id} "
                    f"({player_info.get('profile', {}).get('personaname', 'Unknown')})"
                )
            except Exception as e:
                print(f"Failed to migrate player {account_id}: {e}")
    finally:
        await api.close()

if __name__ == '__main__':
    asyncio.run(migrate_players())
