"""Match filters for the Dota 2 match observer."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import time


class MatchFilter(ABC):
    """Base class for match filters."""
    
    @abstractmethod
    def filter(self, match: Dict[str, Any]) -> bool:
        """Return True if match should be included."""
        pass


class LastThreeMonthsFilter(MatchFilter):
    """Filter matches from the last three months."""
    
    def filter(self, match: Dict[str, Any]) -> bool:
        """Return True if match is from the last three months."""
        current_time = int(time.time())
        three_months_ago = current_time - (90 * 24 * 60 * 60)
        return match.get('start_time', 0) >= three_months_ago
