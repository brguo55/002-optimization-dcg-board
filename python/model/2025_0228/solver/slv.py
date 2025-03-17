# solver.py

# solver.py

import gurobipy as gp
from gurobipy import GRB

#####################################
# Helper function to check keywords
#####################################
def has_keyword(keywords_list, index, code):
    """
    Returns True if 'code' is in keywords_list[index].
    keywords_list[index] should be a list/set of integers.
    """
    return (code in keywords_list[index])

def run_single_turn(
    m, n, h,             # m = #friendly on board, n = #enemy on board, h = #cards in hand
    M,                   # Mana available
    H_hero,              # Enemy hero health
    A, B,                # Attack/Health of friendly minions (size = m+h)
    P, Q,                # Attack/Health of enemy minions (size = n)
    C, S,                # Mana costs + strategic values for the h cards
    weights=None,
    friendly_keywords=None,   # A list of lists: friendly_keywords[i] -> [codes...]
    enemy_keywords=None       # A list of lists: enemy_keywords[j] -> [codes...]
):
    """
    Builds and solves a one-turn optimization model with:
      - Taunt (keyword=3)
      - Divine Shield (keyword=4)
      - (Optional) placeholders for Charge=1, Rush=2

    :param friendly_keywords: a list of length m,
         where friendly_keywords[i] is a list of keyword codes for minion i.
    :param enemy_keywords: a list of length n,
         where enemy_keywords[j] is a list of keyword codes for minion j.

    The rest matches your usual definitions.
    """

    # 1) Default weights if none provided
    if weights is None:
        weights = {
            "W1": 10,  # kill hero
            "W2":  9,  # board clear
            "W3":  8,  # face damage
            "W4":  7,  # penalty for leaving enemy minions
            "W5":  2,  # reward for friendly minion survival
            "W6":  6,  # reward for damaging enemy minions
            "W7":  1,  # penalty for taking damage on trades
            "W8":  4   # reward for playing cards
        }

    W1 = weights["W1"]
    W2 = weights["W2"]
    W3 = weights["W3"]
    W4 = weights["W4"]
    W5 = weights["W5"]
    W6 = weights["W6"]
    W7 = weights["W7"]
    W8 = weights["W8"]

    # 2) Default to empty keyword lists if none given
    if friendly_keywords is None:
        # We'll assume only the m board minions might have keywords
        # (hand minions could too, but you can expand as needed)
        friendly_keywords = [[] for _ in range(m)]
    if enemy_keywords is None:
        enemy_keywords = [[] for _ in range(n)]

    # 3) Create model
    model = gp.Model("KeywordsOptimizationModel")

    # 4) Decision variables
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  # minion i attacks hero
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")        # 1=hero alive, 0=dead
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")         # minion i attacks minion j
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")            # friendly minion i survives
    z = model.addVars(n, vtype=GRB.BINARY, name="z")              # enemy minion j survives
    u = model.addVars(h, vtype=GRB.BINARY, name="u")              # card k played
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")           # board clear indicator

    # 5) Objective function
    objective = (
        # hero kill => (1 - z_hero) * W1
        W1 * (1 - z_hero)
        # board clear => c_ * W2
        + W2 * c_
        # face damage => sum(A[i]*x_hero[i]) * W3
        + W3 * gp.quicksum(A[i]*x_hero[i] for i in range(m+h))
        # penalty for leaving enemy minions => -W4 * sum(P[j]*z[j])
        - W4 * gp.quicksum(P[j]*z[j] for j in range(n))
        # reward for friendly minion survival => +W5 * sum(B[i]*y[i])
        + W5 * gp.quicksum(B[i]*y[i] for i in range(m+h))
        # reward for damaging enemy minions => +W6 * sum(A[i]*x[i,j])
        + W6 * gp.quicksum(A[i]*x[i,j] for i in range(m+h) for j in range(n))
        # penalty for your minions taking damage => -W7 * sum(P[j]*x[i,j])
        - W7 * gp.quicksum(P[j]*x[i,j] for i in range(m+h) for j in range(n))
        # reward for playing cards => +W8 * sum(S[k]*u[k])
        + W8 * gp.quicksum(S[k]*u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # 6) Constraints

    # (1) Each existing friendly minion i can only attack once (hero or exactly one minion)
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i,j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (2) Friendly minion survival
    for i in range(m):
        for j_ in range(n):
            # normal lethal check:
            #   y[i] <= 1 - ((P[j_] - B[i] +1)/P[j_]) * x[i,j_]
            # if minion i has DS (keyword=4), we nullify lethal for them
            lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
            if lethal_factor < 0:
                lethal_factor = 0  # in case P[j_] < B[i], no lethal anyway

            hasDS = has_keyword(friendly_keywords, i, 4)
            # if hasDS => minion can't die from this single attack => multiply factor by (1 - hasDS)
            ds_multiplier = 0 if hasDS else 1

            model.addConstr(
                y[i] <= 1 - lethal_factor * x[i,j_] * ds_multiplier,
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (3) Enemy minion survival
    #    sum(A[i]) / Q[j_] >=1 => z[j_] =0
    # if enemy has DS => it can't be killed from that single chunk of damage
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i]/max(Q[j_],1))*x[i,j_] for i in range(m+h))
        hasDS_enemy = has_keyword(enemy_keywords, j_, 4)
        ds_multiplier_e = 0 if hasDS_enemy else 1

        # z[j] <= 1 - damage_fraction * ds_multiplier_e
        model.addConstr(
            z[j_] <= 1 - damage_fraction * ds_multiplier_e,
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (4) Board clear
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # (5) Enemy hero survival
    model.addConstr(
        z_hero <= 1 - gp.quicksum((A[i]/max(H_hero,1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (6) Board limit: can't have more than 7 friendly minions
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (7) If minion i>=m ended with y[i]=1 => must have been played => u[i-m]
    for i in range(m, m+h):
        model.addConstr(
            y[i] <= u[i-m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (8) Total mana cost <= M
    model.addConstr(
        gp.quicksum(u[k]*C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (9) Newly summoned minions can't attack if they don't have Charge or Rush
    # In your old code, you forced x_hero[i]=0 and x[i,j]=0 for i >=m
    # We'll modify that to allow if has Charge=1 or Rush=2
    for i in range(m, m+h):
        # If we DO NOT have Charge => we can't attack hero
        # If we have Rush => we can only attack minions, not hero
        hasCharge = False
        hasRush   = False
        # we only care about the "new" minions i>=m that are from the hand
        if i < m:
            # i is an old minion on board => no restrictions beyond normal
            continue
        # i-m is the index in hand => we have no "keywords" for them by default, or you can store
        # them in friendly_keywords if you want to allow playing minions with keywords.
        # For demonstration, let's skip the logic if you haven't stored them.

        # Then do:
        # if hasCharge => skip hero block
        # if hasRush => skip minion block
        # else => forbid all attacks

        # For now, to keep it consistent with your old approach, we do:
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i,j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # (10) A minion from hand must be played (u[i-m]=1) to attack
    for i in range(m, m+h):
        if i >= m:
            model.addConstr(
                x_hero[i] <= u[i-m],
                name=f"HandMinionAttackHero_{i}"
            )
            for j_ in range(n):
                model.addConstr(
                    x[i,j_] <= u[i-m],
                    name=f"HandMinionAttackMinion_{i}_{j_}"
                )

    # TAUNT Constraints
    #  - If an enemy minion j hasKeyword=3 (Taunt) and is alive (z[j]=1), you cannot:
    #     1) Attack the hero
    #     2) Attack other non-taunt minions
    # We'll do a single summation of all alive taunt minions:
    for i in range(m):
        # For hero attacks:
        model.addConstr(
            x_hero[i] <= 1 - gp.quicksum(
                z[j_]*1 for j_ in range(n) if has_keyword(enemy_keywords, j_, 3)
            ),
            name=f"NoHeroAttackIfAnyTauntAlive_{i}"
        )

        # For attacks on non-taunt minions:
        for j_ in range(n):
            if not has_keyword(enemy_keywords, j_, 3):
                # If there's ANY alive Taunt minion, can't attack j_
                model.addConstr(
                    x[i,j_] <= 1 - gp.quicksum(
                        z[k]*1 for k in range(n) if has_keyword(enemy_keywords, k, 3)
                    ),
                    name=f"MustAttackTauntFirst_{i}_{j_}"
                )

    # 7) Optimize
    model.optimize()

    # 8) Collect results
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

        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        for i in range(m+h):
            for j_ in range(n):
                result["x_minions"][(i,j_)] = x[i,j_].X

        result["z_hero"] = z_hero.X

        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X

        result["c_clear"] = c_.X

        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result

