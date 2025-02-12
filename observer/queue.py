"""Queue management for the Dota 2 match observer."""
import json
import time
from typing import Optional, List, Dict
from pathlib import Path
import logging
from collections import deque

from .models import QueueItem


class QueueManager:
    """Manages the match processing queue."""
    
    def __init__(self, queue_file: Path, max_retries: int = 3):
        self.queue_file = queue_file
        self.max_retries = max_retries
        self.queue = deque()
        self.logger = logging.getLogger(__name__)
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from file if it exists."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file) as f:
                    items = json.load(f)
                self.queue = deque(
                    QueueItem(**item) for item in items
                )
                self.logger.info(f"Loaded {len(self.queue)} items from queue")
            except Exception as e:
                self.logger.error(f"Failed to load queue: {e}")
    
    def _save_queue(self):
        """Save queue to file."""
        try:
            items = [vars(item) for item in self.queue]
            with open(self.queue_file, 'w') as f:
                json.dump(items, f)
        except Exception as e:
            self.logger.error(f"Failed to save queue: {e}")
    
    def add_match(self, match_id: int, priority: int = 0):
        """Add a match to the queue."""
        item = QueueItem(
            match_id=match_id,
            added_at=time.time(),
            priority=priority
        )
        self.queue.append(item)
        self._save_queue()
    
    def get_next_match(self) -> Optional[QueueItem]:
        """Get next match to process, considering priority and retries."""
        if not self.queue:
            return None
            
        # Sort by priority and retry count
        sorted_queue = sorted(
            self.queue,
            key=lambda x: (x.priority, -x.retry_count)
        )
        self.queue = deque(sorted_queue)
        return self.queue.popleft()
    
    def retry_match(self, item: QueueItem):
        """Add match back to queue for retry."""
        if item.retry_count < self.max_retries:
            item.retry_count += 1
            item.last_retry = time.time()
            self.queue.append(item)
            self._save_queue()
        else:
            self.logger.warning(
                f"Match {item.match_id} exceeded max retries"
            )
