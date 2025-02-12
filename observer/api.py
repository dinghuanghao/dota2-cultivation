"""API client for the Dota 2 match observer."""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging
import time
from .exceptions import DotaAPIError, RateLimitError, MatchNotFoundError
from .models import Match, PlayerMatch


class DotaAPI:
    """Client for interacting with Dota 2 APIs."""

    def __init__(self, base_url: str, match_details_url: str):
        self.base_url = base_url
        self.match_details_url = match_details_url
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        self.min_request_interval = 1  # seconds

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

    async def get_player_matches(self, account_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent matches for a player."""
        await self._rate_limit()
        url = f"{self.base_url}/players/{account_id}/matches"
        
        try:
            async with self.session.get(url, params={"limit": limit}) as response:
                if response.status == 429:
                    raise RateLimitError("OpenDota API rate limit exceeded")
                if response.status != 200:
                    raise DotaAPIError(f"Failed to get player matches: {response.status}")
                return await response.json()
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
