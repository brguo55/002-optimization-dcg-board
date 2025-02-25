import random

class AIPlayer:
    def __init__(self, game_state):
        self.game_state = game_state

    def choose_action(self):
        """Chooses an action based on the current game state."""
        if self.game_state.mana >= 5:
            return "Play High Mana Card"
        elif len(self.game_state.board) < 7:
            return "Summon Minion"
        elif self.game_state.hero_health < 10:
            return "Defend"
        return random.choice(["Attack", "Play Spell", "End Turn"])
