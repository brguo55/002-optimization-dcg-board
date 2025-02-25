from game_state import GameState

class TurnManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def start_turn(self):
        """Processes the beginning of the turn (mana increase, card draw)."""
        print("\n--- Start of Turn ---")
        self.game_state.update_mana()
        self.game_state.draw_card()
        self.game_state.update_board()
        self.game_state.display_state()

    def execute_turn(self):
        """Executes the turn (Placeholder for AI or player moves)."""
        print("--- Turn Execution (AI Actions will be added later) ---")
        # Placeholder for future AI decision-making
        pass  

    def end_turn(self):
        """Processes the end of the turn (Apply any end-of-turn effects)."""
        print("--- End of Turn ---")
        self.game_state.update_board()
        self.game_state.display_state()
