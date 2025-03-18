# solver.py

import gurobipy as gp
from gurobipy import GRB

#####################################
# Helper function to check keywords
#####################################
def has_keyword(keywords_list, index, keyword_str):
    """
    Returns True if 'keyword_str' is present in keywords_list[index].
    Each keywords_list[index] is a list of strings (e.g. ["Taunt","Divine Shield"]).
    """
    return (keyword_str in keywords_list[index])

def run_single_turn(
    m, n, h,
    M, H_hero,
    A, B, P, Q, C, S,
    weights=None,
    friendly_keywords=None,
    enemy_keywords=None
):
    """
    Solve one turn with string-based keywords:
      - "Taunt": Must kill taunt minions before attacking hero or non-taunt minions.
      - "Divine Shield": Ignores lethal once in this simplified model.
      - "Charge" / "Rush": Placeholders if you want newly-summoned minions to attack.

    :param m: # of friendly minions on board
    :param n: # of enemy minions on board
    :param h: # of cards in hand
    :param M: Mana available
    :param H_hero: Enemy hero's health
    :param A,B: Attack/Health of (m+h) friendly minions
    :param P,Q: Attack/Health of n enemy minions
    :param C,S: Mana costs & strategic values for h cards
    :param weights: dict of weighting factors (W1..W8). If None, defaults used
    :param friendly_keywords: list of length m => each entry is a list of keyword strings
    :param enemy_keywords: list of length n => each entry is a list of keyword strings
    :return: Dict with solver results
    """

    # 1) Default weights if none provided
    if weights is None:
        weights = {
            "W1": 10,  # reward for killing hero => (1 - z_hero)
            "W2":  9,  # reward for board clear => c_
            "W3":  8,  # reward for attacking hero => sum(A[i]*x_hero[i])
            "W4":  7,  # penalty for leaving enemy minions alive => - sum(P[j]*z[j])
            "W5":  2,  # reward for your minions surviving => sum(B[i]*y[i])
            "W6":  6,  # reward for minion->minion damage => sum(A[i]*x[i,j])
            "W7":  1,  # penalty for your minions taking damage => - sum(P[j]*x[i,j])
            "W8":  4   # reward for playing cards => sum(S[k]*u[k])
        }

    W1 = weights["W1"]
    W2 = weights["W2"]
    W3 = weights["W3"]
    W4 = weights["W4"]
    W5 = weights["W5"]
    W6 = weights["W6"]
    W7 = weights["W7"]
    W8 = weights["W8"]

    # 2) Default to empty keyword lists if not provided
    if friendly_keywords is None:
        friendly_keywords = [[] for _ in range(m)]
    if enemy_keywords is None:
        enemy_keywords = [[] for _ in range(n)]

    model = gp.Model("KeywordsSolver")

    # 3) Decision Variables
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  # i attacks hero
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")       # 1=hero alive, 0=dead
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")        # i attacks j
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")           # friendly minion i alive
    z = model.addVars(n, vtype=GRB.BINARY, name="z")             # enemy minion j alive
    u = model.addVars(h, vtype=GRB.BINARY, name="u")             # card k is played
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")          # board clear

    # 4) Objective
    objective = (
        # hero kill => W1*(1 - z_hero)
        W1 * (1 - z_hero)
        # board clear => W2*c_
        + W2 * c_
        # face damage => W3 * sum(A[i]*x_hero[i])
        + W3 * gp.quicksum(A[i]*x_hero[i] for i in range(m+h))
        # penalty for leaving enemy minions => -W4 * sum(P[j]*z[j])
        - W4 * gp.quicksum(P[j]*z[j] for j in range(n))
        # reward for friendly survival => W5 * sum(B[i]*y[i])
        + W5 * gp.quicksum(B[i]*y[i] for i in range(m+h))
        # reward for minion->minion damage => W6
        + W6 * gp.quicksum(A[i]*x[i,j] for i in range(m+h) for j in range(n))
        # penalty for your minions taking damage => -W7
        - W7 * gp.quicksum(P[j]*x[i,j] for i in range(m+h) for j in range(n))
        # reward for playing cards => W8
        + W8 * gp.quicksum(S[k]*u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # 5) Constraints

    # (1) Each *on-board* friendly minion can attack at most once (hero or exactly one enemy)
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i,j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (2) Friendly minion survival
    #     If P[j] >= B[i], it would kill your minion i, except if i has "Divine Shield"
    for i in range(m):
        for j_ in range(n):
            lethal_factor = (P[j_] - B[i] + 1) / max(P[j_],1)
            if lethal_factor < 0:
                lethal_factor = 0
            if has_keyword(friendly_keywords, i, "Divine Shield"):
                ds_multiplier = 0  # means ignore lethal this turn
            else:
                ds_multiplier = 1
            model.addConstr(
                y[i] <= 1 - lethal_factor * x[i,j_] * ds_multiplier,
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (3) Enemy minion survival
    #     If total damage fraction >= 1 => z[j_] = 0, except if j has "Divine Shield"
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i]/max(Q[j_],1)) * x[i,j_] for i in range(m+h))
        if has_keyword(enemy_keywords, j_, "Divine Shield"):
            ds_multiplier_e = 0
        else:
            ds_multiplier_e = 1
        model.addConstr(
            z[j_] <= 1 - damage_fraction * ds_multiplier_e,
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (4) Board clear => c_ = 1 iff all enemy minions are dead
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # (5) Enemy hero survival => if sum of fraction >=1 => z_hero=0
    model.addConstr(
        z_hero <= 1 - gp.quicksum((A[i]/max(H_hero,1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (6) Board limit => at most 7 friendly minions total (existing + new)
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (7) If a newly played minion (i >= m) survived => must have been played => u[i - m]
    for i in range(m, m+h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (8) Mana limit => sum of played cards <= M
    model.addConstr(
        gp.quicksum(u[k]*C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (9) Newly summoned minions can't attack if no "Charge"/"Rush"
    # For simplicity, we forbid all attacks from new minions.
    for i in range(m, m+h):
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i,j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # (10) Must be played to attack
    for i in range(m, m+h):
        if i >= m:
            # i is from hand => must have u[i-m]=1 to attack
            model.addConstr(
                x_hero[i] <= u[i-m],
                name=f"HandMinionAttackHero_{i}"
            )
            for j_ in range(n):
                model.addConstr(
                    x[i,j_] <= u[i-m],
                    name=f"HandMinionAttackMinion_{i}_{j_}"
                )

    # --- TAUNT Constraints ---
    # If ANY enemy minion with "Taunt" is alive => must kill them first
    for i in range(m):
        # A) Forbid attacking hero if any taunt is alive
        model.addConstr(
            x_hero[i] <= 1 - gp.quicksum(
                z[j_] for j_ in range(n)
                if has_keyword(enemy_keywords, j_, "Taunt")
            ),
            name=f"NoHeroAttackIfTaunt_{i}"
        )

        # B) Forbid attacking non-taunt minions if any taunt is alive
        for j_ in range(n):
            if not has_keyword(enemy_keywords, j_, "Taunt"):
                model.addConstr(
                    x[i,j_] <= 1 - gp.quicksum(
                        z[k] for k in range(n)
                        if has_keyword(enemy_keywords, k, "Taunt")
                    ),
                    name=f"MustKillTauntFirst_{i}_{j_}"
                )

    # 6) Optimize
    model.optimize()

    # 7) Collect results
    result = {
        "status": model.status,
        "objective": None,
        "x_hero": {},
        "x_minions": {},
        "z_hero": None,
        "z_enemy": {},
        "c_clear": None,
        "y_survive": {},
        "cards_played": {}
    }

    if model.status == GRB.OPTIMAL:
        result["objective"] = model.objVal

        # Attacks on hero
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        # Attacks on minions
        for i in range(m+h):
            for j_ in range(n):
                result["x_minions"][(i, j_)] = x[i, j_].X

        # Hero alive?
        result["z_hero"] = z_hero.X

        # Enemy minions alive?
        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X

        # Board clear?
        result["c_clear"] = c_.X

        # Friendly minion survival
        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        # Cards played
        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result
