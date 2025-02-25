from game import GameState
from ai import AIPlayer
from gurobi_helper import GurobiSolver

# Initialize game state
game = GameState()
game.update_mana()
game.draw_card(["Fireball", "Minion", "Heal"])

# AI Decision Logic
ai = AIPlayer(game)
chosen_action = ai.choose_action()
print("AI Chose:", chosen_action)

# Optimization-based decision-making
optimizer = GurobiSolver(game)
best_action = optimizer.optimize_turn()
print("Gurobi Suggests:", best_action)
