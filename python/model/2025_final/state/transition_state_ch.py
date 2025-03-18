# transition_state.py

from scenarios.deck_1 import deck, add_card_to_hand
from solver.slv import run_single_turn  # The function above

def start_turn(hero, deck, hand_list):
    if deck:
        new_card = add_card_to_hand(deck, hand_list)
        print(f"{hero.hero_class} draws: {new_card}")


def apply_results(solution, scenario_data):
    """
    解释从 run_single_turn 返回的求解结果，
    并更新游戏状态（如英雄血量、随从存活等）。
    同时打印输出哪些随从攻击了哪些目标、以及最终的状态。
    """

    # 检查求解器状态
    if solution["status"] != 2:  # 2 => GRB.OPTIMAL（最优解）
        print("No valid solution. Status:", solution["status"])
        return

    # 打印目标函数的值
    print(f"Objective: {solution['objective']}")

    # --- 对敌方英雄的攻击 ---
    # 如果在 solution 中存在 "x_hero" 这一部分
    if "x_hero" in solution:
        for i, val in solution["x_hero"].items():
            if val > 0.5:  # 将大于0.5的值视为1
                dmg = scenario_data["A"][i]
                print(f"Friendly minion {i} attacked the enemy hero for {dmg} damage.")
                scenario_data["H_hero"] -= dmg

    # --- 对敌方随从的攻击 ---
    # 如果在 solution 中存在 "x_minions" 这一部分
    if "x_minions" in solution:
        for (i, j), val in solution["x_minions"].items():
            if val > 0.5:  # 将大于0.5的值视为1
                dmg = scenario_data["A"][i]
                print(f"Friendly minion {i} attacked enemy minion {j} for {dmg} damage.")
                scenario_data["Q"][j] -= dmg

    # --- 打印敌方英雄最终的血量 ---
    print(f"Enemy hero health is now {scenario_data['H_hero']}.")
    if scenario_data["H_hero"] <= 0:
        print("The enemy hero has died!")

    # --- 打印敌方随从的最终血量 ---
    for j, health in enumerate(scenario_data["Q"]):
        print(f"Enemy minion {j} health: {health}")
        if health <= 0:
            print(f"Enemy minion {j} has died (health <= 0).")

    # --- 打印哪些友方随从幸存 ---
    # 'y_survive' 是一个字典：{ i: 0/1 }，表示每个友方（或新召唤）随从的生存状态
    if "y_survive" in solution:
        print("\nFriendly minions after combat:")
        for i, alive_val in solution["y_survive"].items():
            if alive_val > 0.5:
                # 我们并未在本模型中跟踪友方随从的剩余血量，因此只能显示原始Attack/Health
                atk = scenario_data["A"][i]
                hp = scenario_data["B"][i]
                print(f"  Friendly minion {i} survived with Attack={atk}, Health={hp}.")
            else:
                print(f"  Friendly minion {i} did NOT survive (y_survive[{i}] = 0).")

    # 'z_enemy' 是一个字典：{ j: 0/1 }，表示每个敌方随从的生存状态
    if "z_enemy" in solution:
        print("\nEnemy minions after combat:")
        for j, z_val in solution["z_enemy"].items():
            if z_val > 0.5:
                # 表示该敌方随从在模型结果中仍然存活
                print(f"  Enemy minion {j} is still alive (z_enemy[{j}] = 1), "
                      f"updated Health={scenario_data['Q'][j]}.")
            else:
                print(f"  Enemy minion {j} is considered dead (z_enemy[{j}] = 0).")


def end_turn(hero, opponent_hero):
    """
    回合结束时的检查，例如对方英雄或己方英雄是否血量降至0而死亡。
    """
    if opponent_hero.health <= 0:
        print(f"{opponent_hero.hero_class} has died!")
    if hero.health <= 0:
        print(f"{hero.hero_class} has died!")


def swap_roles(hero1, hero2):
    """
    返回 (hero2, hero1)，用于交换当前回合英雄和对方英雄。
    """
    return hero2, hero1


def run_one_turn(scenario_data):
    """
    当你只想对 scenario_data 运行一次求解器时的便捷函数。
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
        # 以及任何 W1..W7 的参数
    )
    return result
