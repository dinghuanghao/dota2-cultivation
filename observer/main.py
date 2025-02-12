"""Main observer implementation for the Dota 2 match observer."""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
from collections import deque

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
        self.detail_queue = deque()  # Queue for matches needing details
        self.match_filters: List[Callable[[Dict[str, Any]], bool]] = [
            self.filter_last_three_months
        ]

    @staticmethod
    def filter_last_three_months(match: Dict[str, Any]) -> bool:
        """Filter matches from the last three months."""
        current_time = int(time.time())
        three_months_ago = current_time - (90 * 24 * 60 * 60)  # 90 days in seconds
        return match.get('start_time', 0) >= three_months_ago

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

    def filter_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all registered filters to matches."""
        filtered_matches = matches
        for filter_func in self.match_filters:
            filtered_matches = [m for m in filtered_matches if filter_func(m)]
        return filtered_matches

    async def initialize_detail_queue(self):
        """Initialize the detail queue with matches from all players."""
        try:
            players = self.load_player_list()
            for player_id in players:
                self.logger.info(f"Fetching initial matches for player {player_id}")
                matches = await self.api.get_player_matches(player_id)
                filtered_matches = self.filter_matches(matches)
                
                self.logger.info(
                    f"Found {len(filtered_matches)} matches to process "
                    f"out of {len(matches)} total matches for player {player_id}"
                )
                
                for match in filtered_matches:
                    if not self.db.is_match_stored(match["match_id"]):
                        self.detail_queue.append(match["match_id"])
                        
        except Exception as e:
            self.logger.error(f"Error initializing detail queue: {e}")

    async def check_new_matches(self):
        """Check for new matches from all players."""
        try:
            players = self.load_player_list()
            for player_id in players:
                self.logger.info(f"Checking new matches for player {player_id}")
                matches = await self.api.get_player_matches(player_id, limit=50)
                filtered_matches = self.filter_matches(matches)
                
                for match in filtered_matches:
                    if not self.db.is_match_stored(match["match_id"]):
                        self.detail_queue.append(match["match_id"])
                        self.logger.info(f"Added new match {match['match_id']} to queue")
                
        except Exception as e:
            self.logger.error(f"Error checking new matches: {e}")

    async def process_detail_queue(self):
        """Process matches in the detail queue."""
        while self.detail_queue:
            match_id = self.detail_queue.popleft()
            try:
                self.logger.info(f"Processing match {match_id} from queue")
                await self.process_match(match_id)
            except Exception as e:
                self.logger.error(f"Error processing match {match_id}: {e}")
                # Add back to queue on failure
                self.detail_queue.append(match_id)

    async def run(self):
        """Main run loop."""
        try:
            # Initialize API session
            await self.api.init()
            
            # Initial load of all matches
            await self.initialize_detail_queue()
            
            while True:
                # Process any matches in the queue
                while self.detail_queue:
                    await self.process_detail_queue()
                
                # Check for new matches
                await self.check_new_matches()
                
                # Wait before next check
                await asyncio.sleep(self.config.POLLING_INTERVAL)
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(self.config.RETRY_DELAY)
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources."""
        await self.api.close()
