"""Test script for database API."""
from observer.db_api import DatabaseAPI
from observer.database import Database
from observer.models import Match, MatchPlayer
from pathlib import Path

def test_api():
    """Test database API functionality."""
    api = DatabaseAPI()
    db = Database(Path(__file__).parent / "matches.db")

    # Test default player exists
    default_player = db.get_player(455681834)
    assert default_player is not None, "Default player should exist"
    assert default_player.account_id == 455681834
    assert default_player.personaname is not None
    print("Default player test passed")

    # Test pagination
    total, matches = api.get_player_matches(455681834)
    assert len(matches) <= 10
    if matches:
        assert isinstance(matches[0], Match)
        assert isinstance(matches[0].players[0], MatchPlayer)
    print("Pagination test passed")

    # Test filtering
    total, filtered_matches = api.get_player_matches_filtered(
        455681834,
        game_mode=1,
        hero_id=1
    )
    if filtered_matches:
        assert isinstance(filtered_matches[0], Match)
        assert isinstance(filtered_matches[0].players[0], MatchPlayer)
    print(f"Found {total} matches with game_mode={1} and hero_id={1}")

    # Test stats
    stats = api.get_player_stats(455681834)
    print(f"Total matches: {stats['total_matches']}")
    win_rate = (stats['wins'] / stats['total_matches'] * 100) if stats['total_matches'] > 0 else 0
    print(f"Win rate: {win_rate:.1f}%")
    if stats['heroes']:
        print(f"Top heroes: {[h['hero_id'] for h in stats['heroes'][:3]]}")

if __name__ == '__main__':
    test_api()
