from scenarios.deck_example import add_card_to_hand
from solver.solver import run_single_turn  # or your solver function

def start_turn(hero, deck, hand_list):
    """
    Start-of-turn:
      - Possibly increment mana (if simulating multi-turn)
      - Draw a card if the deck isn't empty
    """
    # Draw one card for the hero from the specified deck
    if deck:
        new_card = add_card_to_hand(deck, hand_list)
        if new_card:
            print(f"{hero.hero_class} draws: {new_card.name}")
        else:
            print(f"{hero.hero_class} cannot draw; deck is empty.")
    else:
        print(f"{hero.hero_class}'s deck is empty, no card drawn.")

def apply_results(solution, scenario_data, active_hero=None, opp_hero=None):
    """
    Interpret the solver solution from run_single_turn, log the actions,
    update hero health, and remove dead enemy minions from the board.

    Requires scenario_data to have references to:
      - scenario_data["A"] for friendly minion attacks
      - scenario_data["enemy_list"] to remove or update the actual enemy minion objects
        (if you want to physically remove them from the board.)
    """

    if solution["status"] != 2:  # 2 => GRB.OPTIMAL
        print("No valid solution. Status:", solution["status"])
        return

    print(f"Objective: {solution['objective']}")

    # 1) Unpack arrays from scenario_data
    A = scenario_data["A"]  # Attack values for friendly side (size m+h)
    # B = scenario_data["B"] # If needed for your logic
    # P = scenario_data["P"] # Attack for enemy minions (size n)
    # Q = scenario_data["Q"] # Health for enemy minions (size n)

    # Optional: references to actual lists of minion objects, if you want to remove them
    enemy_list = scenario_data.get("enemy_list", None)  # e.g. the actual python list of enemy minions

    # 2) Summarize minion -> hero attacks
    print("\n-- Minion -> Hero Attacks --")
    x_hero = solution.get("x_hero", {})
    total_hero_damage = 0
    for i, val in x_hero.items():
        if val > 0.5:
            dmg = A[i]
            print(f"Friendly minion {i} attacked the hero for {dmg} damage.")
            total_hero_damage += dmg

    # If there's an opposing hero, reduce their health
    if total_hero_damage > 0 and opp_hero:
        opp_hero.health -= total_hero_damage
        print(f"{opp_hero.hero_class} hero's health is now {opp_hero.health}")

    # 3) Summarize minion -> minion attacks
    print("\n-- Minion vs. Minion Attacks --")
    x_minions = solution.get("x_minions", {})
    for (i, j), val in x_minions.items():
        if val > 0.5:
            dmg = A[i]
            print(f"Friendly minion {i} attacked enemy minion {j} for {dmg} damage.")

    # 4) Remove enemy minions that are killed
    #    We assume c_clear[j] = 1 => "enemy minion j is fully killed."
    c_clear = solution.get("c_clear", {})
    if enemy_list is not None:
        print("\n-- Removing dead enemy minions --")
        # Remove from the highest index to the lowest, so popping doesn't shift the indices
        for idx in reversed(range(len(enemy_list))):
            # If we have c_clear and the solver says c_clear[idx] = 1, remove
            if c_clear.get(idx, 0) > 0.5:
                minion = enemy_list[idx]
                print(f"Enemy minion {idx} ({minion.name}) was killed and is removed from the board.")
                enemy_list.pop(idx)

    # If you want to remove your own dead minions (friendly side),
    # you can do a similar approach if you have y_survive or something else.

    print("\n--- End of apply_results ---")


def end_turn(active_hero, opponent_hero):
    """
    End-of-turn checks. If either hero <= 0 HP, announce it.
    """
    if opponent_hero.health <= 0:
        print(f"{opponent_hero.hero_class} has died!")
    if active_hero.health <= 0:
        print(f"{active_hero.hero_class} has died!")

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
    )
    return result