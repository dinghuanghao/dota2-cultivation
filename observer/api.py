"""API client for the Dota 2 match observer."""
import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
import logging
import time
from .exceptions import DotaAPIError, RateLimitError, MatchNotFoundError
from .models import Match


class DotaAPI:
    """Client for interacting with Dota 2 APIs."""

    def __init__(self, base_url: str, match_details_url: str):
        self.base_url = base_url
        self.match_details_url = match_details_url
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        self.min_request_interval = 0.5  # seconds

    async def init(self):
        """Initialize the API client session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the API client session."""
        await self.session.close()

    async def _rate_limit(self):
        """Implement rate limiting."""
        now = time.time()
        if now - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval)
        self.last_request_time = now

    async def get_player_info(self, account_id: int) -> Dict[str, Any]:
        """Get player information from OpenDota API."""
        await self._rate_limit()
        url = f"{self.base_url}/players/{account_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    raise DotaAPIError(f"Player {account_id} not found")
                if response.status == 429:
                    raise RateLimitError("OpenDota API rate limit exceeded")
                if response.status != 200:
                    raise DotaAPIError(f"Failed to get player info: {response.status}")
                
                data = await response.json()
                if not data:
                    raise DotaAPIError(f"Empty response for player {account_id}")
                    
                return data
        except aiohttp.ClientError as e:
            raise DotaAPIError(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise DotaAPIError(f"Invalid JSON response: {e}")

    async def get_player_matches(self, account_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get matches for a player. If limit is None, fetches all matches."""
        await self._rate_limit()
        url = f"{self.base_url}/players/{account_id}/matches"
        params = {"limit": limit} if limit is not None else {}

        try:
            if limit:
                self.logger.info(f"Fetching latest {limit} matches for player {account_id}")
            else:
                self.logger.info(f"Fetching all matches for player {account_id}")

            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    raise RateLimitError("OpenDota API rate limit exceeded")
                if response.status != 200:
                    raise DotaAPIError(f"Failed to get player matches: {response.status}")

                matches = await response.json()
                self.logger.info(f"Total matches found for player {account_id}: {len(matches)}")
                return matches

        except aiohttp.ClientError as e:
            raise DotaAPIError(f"API request failed: {e}")

    async def get_match_details(self, match_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific match."""
        await self._rate_limit()

        try:
            async with self.session.get(
                self.match_details_url,
                params={"matchId": match_id}
            ) as response:
                if response.status == 404:
                    raise MatchNotFoundError(f"Match {match_id} not found")
                if response.status != 200:
                    raise DotaAPIError(f"Failed to get match details: {response.status}")

                data = await response.json()
                if not data.get("result"):
                    raise DotaAPIError("Invalid match data format")

                return data["result"][0]["data"]
        except aiohttp.ClientError as e:
            raise DotaAPIError(f"API request failed: {e}")
