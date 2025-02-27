# turn_manager.py

from solver.turn_solver import run_single_turn
from scenarios.deck_example import add_card_to_hand
# from your "setup_single_turn_data" import or define it here if you prefer

def setup_single_turn_data(m, n, h, M, H_hero, A, B, P, Q, C, S):
    """
    If you want a direct approach, you can pass these arrays from your main code,
    or build them inside. This is just a placeholder function.
    """
    scenario_data = {
        "m": m, "n": n, "h": h,
        "M": M, "H_hero": H_hero,
        "A": A, "B": B, "P": P, "Q": Q,
        "C": C, "S": S
    }
    return scenario_data

def start_turn(hero, deck, hand_list):
    """
    If there's a deck, draw a card. If you have mana to increment, do so here.
    """
    if deck:
        card_drawn = add_card_to_hand(deck, hand_list)
        print(f"{hero.hero_class} draws: {card_drawn}")

def apply_results(solution, scenario_data):
    """
    Applies the solution from run_single_turn to your game state.
    For example, if x_hero[i] = 1, that minion i attacked the hero.
    If cards were played (u[k] = 1), you put them onto the board, etc.
    """
    if solution["status"] != 2:  # 2 = GRB.OPTIMAL
        print("No optimal solution. Status:", solution["status"])
        return

    print(f"Optimal objective: {solution['objective']}")
    # Example: print which minions attacked hero
    for i, val in solution["x_hero"].items():
        if val > 0.5:
            print(f"Minion {i} attacked the hero for {scenario_data['A'][i]} damage.")
    # ... similarly handle x_minions, y_survive, z_dead, etc.

def end_turn(hero, opponent):
    """
    End-of-turn checks, e.g. if hero or opponent <= 0 HP.
    """
    if hero.health <= 0:
        print(f"{hero.hero_class} is dead!")
    if opponent.health <= 0:
        print(f"{opponent.hero_class} is dead!")

def swap_players(hero1, hero2):
    """
    Returns (hero2, hero1), effectively flipping the active roles.
    """
    return hero2, hero1

def run_one_round(hero1, hero2, deck1, deck2, hand1, hand2, arrays1, arrays2, weights=None):
    """
    Demonstrates a single "round" = hero1's turn then hero2's turn, using the
    final model. `arrays1` and `arrays2` are your (m, n, h, M, H_hero, A, B, P, Q, C, S)
    or scenario_data for each side.
    """

    # 1) Hero1's turn
    start_turn(hero1, deck1, hand1)
    scenario_data_1 = setup_single_turn_data(**arrays1)
    solution1 = run_single_turn(**scenario_data_1, weights=weights if weights else {})
    apply_results(solution1, scenario_data_1)
    end_turn(hero1, hero2)

    # 2) Swap roles -> Hero2's turn
    hA, hB = swap_players(hero1, hero2)
    deckA, deckB = deck2, deck1
    handA, handB = hand2, hand1
    arraysA, arraysB = arrays2, arrays1  # etc.

    start_turn(hA, deckA, handA)
    scenario_data_2 = setup_single_turn_data(**arraysA)
    solution2 = run_single_turn(**scenario_data_2, weights=weights if weights else {})
    apply_results(solution2, scenario_data_2)
    end_turn(hA, hB)

    print("One round completed.")
