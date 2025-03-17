# transition_state.py

from scenarios.deck_1 import deck, add_card_to_hand
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

    # --- Attacks on the enemy hero ---
    for i, val in solution["x_hero"].items():
        if val > 0.5:
            dmg = scenario_data["A"][i]
            print(f"Minion {i} attacked the hero for {dmg} damage.")
            # Subtract from the enemy hero's health
            scenario_data["H_hero"] -= dmg

    # --- Attacks on enemy minions ---
    # Assume solution["x"] is a dict with keys (i, j) -> float
    # or a nested dict solution["x"][i][j], adjust accordingly
    if "x" in solution:
        for (i, j), val in solution["x"].items():
            if val > 0.5:
                dmg = scenario_data["A"][i]
                print(f"Minion {i} attacked enemy minion {j} for {dmg} damage.")
                # Subtract from enemy minion's health
                scenario_data["Q"][j] -= dmg

    # (Optional) Check if enemy minions died, etc.
    # That depends on how you handle "dead" minions:
    #  if scenario_data["Q"][j] <= 0, then minion j is dead.

    # For demonstration: print updated health
    print(f"Enemy hero health is now {scenario_data['H_hero']}.")
    if scenario_data["H_hero"] <= 0:
        print("Enemy hero has died!")

    for j, health in enumerate(scenario_data["Q"]):
        print(f"Enemy minion {j} health: {health}")
        if health <= 0:
            print(f"Enemy minion {j} has died.")

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
