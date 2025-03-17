# transition_state.py

from scenarios.deck_example import deck_15, add_card_to_hand
from solver.slv import run_single_turn  # The function above

def start_turn(hero, deck, hand_list):
    """
    Example: draw a card, increment mana, etc.
    """
    if deck:
        new_card = add_card_to_hand(deck, hand_list)
        print(f"{hero.hero_class} draws: {new_card}")

def apply_results(solution, scenario_data):
    """
    Interpret the solver solution from run_single_turn
    and update your game state (hero health, minion status, etc.).
    """
    if solution["status"] != 2:  # 2 => GRB.OPTIMAL
        print("No valid solution. Status:", solution["status"])
        return

    print(f"Objective: {solution['objective']}")
    # For example, see which minions attacked the hero
    for i, val in solution["x_hero"].items():
        if val > 0.5:
            dmg = scenario_data["A"][i]
            print(f"Minion {i} attacked the hero for {dmg} damage")
            # scenario_data["opponent_hero"].health -= dmg
    # etc...

def end_turn(hero, opponent_hero):
    """
    End-of-turn checks, e.g. did opponent_hero or hero hit 0 HP?
    """
    if opponent_hero.health <= 0:
        print(f"{opponent_hero.hero_class} has died!")
    if hero.health <= 0:
        print(f"{hero.hero_class} has died!")

def swap_roles(hero1, hero2):
    """
    Returns (hero2, hero1), flipping active and opponent roles
    """
    return hero2, hero1

def run_one_turn(scenario_data):
    """
    A convenience function if you want to just run the solver on scenario_data.
    """
    result = run_single_turn(
        m=scenario_data["m"],
        n=scenario_data["n"],
        h=scenario_data["h"],
        M=scenario_data["M"],
        H_hero=scenario_data["H_hero"],
        A=scenario_data["A"],
        B=scenario_data["B"],
        P=scenario_data["P"],
        Q=scenario_data["Q"],
        C=scenario_data["C"],
        S=scenario_data["S"]
        # plus any W1..W7 arguments
    )
    return result
