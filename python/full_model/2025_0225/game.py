class GameState:
    def __init__(self):
        self.mana = 0
        self.board = []
        self.hand = []
        self.hero_health = 30
        self.opponent_health = 30

    def update_mana(self):
        """Increases mana at the start of the turn, up to 10 max."""
        self.mana = min(self.mana + 1, 10)

    def draw_card(self, deck):
        """Draws a card if the deck is not empty."""
        if deck:
            self.hand.append(deck.pop(0))
        else:
            print("No cards left!")

    def update_board(self):
        """Removes dead minions and applies effects."""
        self.board = [minion for minion in self.board if minion.health > 0]
