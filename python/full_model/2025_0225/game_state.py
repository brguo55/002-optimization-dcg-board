class GameState:
    def __init__(self):
        self.mana = 0
        self.board = []
        self.hand = []
        self.hero_health = 30
        self.opponent_health = 30
        self.deck = ["Fireball", "Minion", "Heal", "Shield", "Spell Boost"]

    def update_mana(self):
        """Increases mana at the start of the turn, up to a maximum of 10."""
        self.mana = min(self.mana + 1, 10)

    def draw_card(self):
        """Draws a card from the deck if available."""
        if self.deck:
            drawn_card = self.deck.pop(0)
            self.hand.append(drawn_card)
            print(f"Card Drawn: {drawn_card}")
        else:
            print("No cards left to draw!")

    def update_board(self):
        """Removes minions with 0 HP and applies any turn-based effects."""
        self.board = [minion for minion in self.board if minion["health"] > 0]

    def display_state(self):
        """Prints the current game state for debugging."""
        print(f"Mana: {self.mana}, Hero Health: {self.hero_health}, Hand: {self.hand}, Board: {self.board}")
