"""Main entry point for the Dota 2 match observer."""
import asyncio
import logging
from .main import MatchObserver
from .config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    config = Config()
    observer = MatchObserver(config)
    try:
        await observer.api.init()
        await observer.run()
    except KeyboardInterrupt:
        logging.info("Shutting down observer...")
    finally:
        await observer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
