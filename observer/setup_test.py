"""Setup script for testing the observer."""
from pathlib import Path
import json

def setup_test_data():
    """Create initial player list for testing."""
    player_list = ['455681834', '76561198134743556']
    with open(Path(__file__).parent / 'player_list.json', 'w') as f:
        json.dump(player_list, f)

if __name__ == '__main__':
    setup_test_data()
