from game_state import GameState
from turn import TurnManager

# Initialize the game state
game = GameState()
turn_manager = TurnManager(game)

# Execute a single turn
turn_manager.start_turn()
turn_manager.execute_turn()
turn_manager.end_turn()
