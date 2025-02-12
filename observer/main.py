"""Main observer implementation for the Dota 2 match observer."""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .config import Config
from .database import Database
from .api import DotaAPI
from .models import Match, PlayerMatch
from .exceptions import DotaAPIError, RateLimitError, MatchNotFoundError


class MatchObserver:
    """Main observer class that coordinates match data collection."""

    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.DATABASE_PATH)
        self.api = DotaAPI(config.OPENDOTA_BASE_URL, config.MATCH_DETAILS_URL)
        self.logger = logging.getLogger(__name__)

    def load_player_list(self) -> List[int]:
        """Load the list of player IDs to monitor."""
        try:
            with open(self.config.PLAYER_LIST_PATH) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load player list: {e}")
            raise

    async def process_match(self, match_id: int):
        """Process a single match."""
        if self.db.is_match_stored(match_id):
            return

        try:
            match_data = await self.api.get_match_details(match_id)
            player_matches = []
            for player in match_data.get("players", []):
                player_matches.append(PlayerMatch(
                    match_id=match_id,
                    account_id=player.get("account_id", 0),
                    hero_id=player.get("hero_id", 0),
                    player_slot=player.get("player_slot", 0),
                    kills=player.get("kills", 0),
                    deaths=player.get("deaths", 0),
                    assists=player.get("assists", 0),
                    gold_per_min=player.get("gold_per_min", 0),
                    xp_per_min=player.get("xp_per_min", 0),
                    last_hits=player.get("last_hits", 0),
                    denies=player.get("denies", 0)
                ))
            
            match = Match(
                match_id=match_id,
                start_time=match_data.get("start_time", 0),
                duration=match_data.get("duration", 0),
                game_mode=match_data.get("game_mode", 0),
                radiant_win=bool(match_data.get("radiant_win", False)),
                radiant_score=match_data.get("radiant_score", 0),
                dire_score=match_data.get("dire_score", 0)
            )
            
            self.db.store_match(match, player_matches)
            self.logger.info(f"Stored match {match_id}")
        except MatchNotFoundError:
            self.logger.warning(f"Match {match_id} not found")
        except Exception as e:
            self.logger.error(f"Error processing match {match_id}: {e}")

    async def process_player_matches(self, account_id: int):
        """Process recent matches for a player."""
        try:
            self.logger.info(f"Fetching matches for player {account_id}")
            matches = await self.api.get_player_matches(account_id)
            total_matches = len(matches)
            
            # Filter matches from last 3 months
            current_time = int(time.time())
            three_months_ago = current_time - (90 * 24 * 60 * 60)  # 90 days in seconds
            recent_matches = [
                match for match in matches 
                if match.get('start_time', 0) >= three_months_ago
            ]
            
            self.logger.info(
                f"Found {len(recent_matches)} matches within last 3 months "
                f"out of {total_matches} total matches for player {account_id}"
            )
            
            for match in recent_matches:
                self.logger.info(f"Processing match {match['match_id']}")
                await self.process_match(match["match_id"])
                
        except RateLimitError:
            self.logger.warning("Rate limit reached, waiting before retry")
            await asyncio.sleep(self.config.RETRY_DELAY)
        except Exception as e:
            self.logger.error(f"Error processing player {account_id}: {e}")

    async def run(self):
        """Main run loop."""
        while True:
            try:
                players = self.load_player_list()
                for player_id in players:
                    await self.process_player_matches(player_id)
                    await asyncio.sleep(self.config.POLLING_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.config.RETRY_DELAY)

    async def cleanup(self):
        """Cleanup resources."""
        await self.api.close()
