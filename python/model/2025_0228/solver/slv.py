# solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m, n, h, M, H_hero,
    A, B, P, Q, C, S,
    weights=None
):
    """
    Solve one turn, returning a solution dict.

    :param m: Number of friendly minions on board
    :param n: Number of enemy minions on board
    :param h: Number of cards in hand
    :param M: Mana available this turn
    :param H_hero: Enemy hero's current health
    :param A: List of Attack values for (m+h) friendly minions (board + hand)
    :param B: List of Health values for (m+h) friendly minions (board + hand)
    :param P: List of Attack values for n enemy minions
    :param Q: List of Health values for n enemy minions
    :param C: List of Mana costs for the h cards in hand
    :param S: List of "strategic values" for the h cards in hand
    :param weights: Optional dict of weighting factors, e.g.:
                    {
                        "W1": 10,
                        "W2": 9,
                        "W3": 8,
                        "W4": 7,
                        "W5": 6,
                        "W6": 5,
                        "W7": 4,
                        "W8": 3
                    }

    :return: A dictionary with:
        {
            "status": model.status,
            "objective": model.objVal (if OPTIMAL),
            "x_hero": { i: 0/1 },
            "x_minions": { (i, j): 0/1 },
            "z_hero": 0/1,
            "z_enemy": { j: 0/1 },
            "c_clear": 0/1,
            "y_survive": { i: 0/1 },
            "cards_played": { k: 0/1 }
        }
    """

    # 1) If no weights provided, use defaults
    if weights is None:
        weights = {
            "W1": 10,
            "W2": 9,
            "W3": 8,
            "W4": 7,
            "W5": 2,
            "W6": 6,
            "W7": 1,
            "W8": 4
        }

    W1 = weights["W1"]
    W2 = weights["W2"]
    W3 = weights["W3"]
    W4 = weights["W4"]
    W5 = weights["W5"]
    W6 = weights["W6"]
    W7 = weights["W7"]
    W8 = weights["W8"]

    # 2) Create model
    model = gp.Model("NewOptimizationModel")

    # Decision Variables
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")    # minion i attacks hero
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")         # enemy hero alive/dead
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")          # minion i attacks minion j
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")             # friendly minion i alive after trades
    z = model.addVars(n, vtype=GRB.BINARY, name="z")               # enemy minion j alive after trades
    u = model.addVars(h, vtype=GRB.BINARY, name="u")               # card k is played
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")            # board clear indicator (1 if all enemy minions dead)

    # 3) Objective Function
    objective = (
    #  --> If z_hero=0 (hero dead), this adds +W1 to the objective.
    #      If z_hero=1 (hero alive), this adds +0.
    W1 * (1 - z_hero)

    # (2) + W2 * c_
    + W2 * c_

    # (3) + W3 * sum(A[i] * x_hero[i])
    + W3 * gp.quicksum(A[i] * x_hero[i] for i in range(m+h))

    # (4) - W4 * sum(P[j] * z[j])
    - W4 * gp.quicksum(P[j] * z[j] for j in range(n))

    # (5) + W5 * sum(B[i] * y[i])
    + W5 * gp.quicksum(B[i] * y[i] for i in range(m+h))

    # (6) + W6 * sum(A[i] * x[i, j])
    + W6 * gp.quicksum(A[i] * x[i, j] for i in range(m+h) for j in range(n))

    # (7) - W7 * sum(P[j] * x[i, j])
    - W7 * gp.quicksum(P[j] * x[i, j] for i in range(m+h) for j in range(n))

    # (8) + W8 * sum(S[k] * u[k])
    + W8 * gp.quicksum(S[k] * u[k] for k in range(h))
)
    model.setObjective(objective, GRB.MAXIMIZE)


    # 4) Constraints

    # Constraint 1: each friendly minion can attack only once (hero or one minion or not at all)
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # Constraint 2: friendly minion survival
    # If a friendly minion i attacks a sufficiently strong enemy minion j, it might die
    for i in range(m):
        for j_ in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j_] - B[i] + 1) / max(P[j_], 1)) * x[i,j_],
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # Constraint 3: enemy minion survival
    # Enough damage => z[j] forced to 0
    for j_ in range(n):
        model.addConstr(
            z[j_] <= 1 - gp.quicksum(
                (A[i] / max(Q[j_], 1)) * x[i, j_] 
                for i in range(m+h)
            ),
            name=f"EnemyMinionSurvival_{j_}"
        )

    # Constraint 4: board clear -> c_ = 1 iff all enemy minions dead (z[j] = 0)
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # Constraint 5: enemy hero survival
    # Enough damage => z_hero = 0
    model.addConstr(
        z_hero <= 1 - gp.quicksum(
            (A[i] / max(H_hero, 1)) * x_hero[i] 
            for i in range(m+h)
        ),
        name="EnemyHeroSurvival"
    )

    # Constraint 6: board limit - at most 7 friendly minions remain at end
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # Constraint 7: if y[i] = 1 for a newly summoned minion (i >= m), then u[i-m] = 1
    for i in range(m, m + h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # Constraint 8: total mana cost of played cards can't exceed M
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # Constraint 9: newly summoned minions can't attack this turn (no Charge/Rush in effect)
    for i in range(m, m+h):
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i, j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # Constraint 10: a minion from hand must be played (u[i-m]=1) before it can attack
    for i in range(m, m+h):
        model.addConstr(
            x_hero[i] <= u[i - m],
            name=f"HandMinionAttackHero_{i}"
        )
        for j_ in range(n):
            model.addConstr(
                x[i, j_] <= u[i - m],
                name=f"HandMinionAttackMinion_{i}_{j_}"
            )

    # 5) Optimize
    model.optimize()

    # 6) Collect Results
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
                result["x_minions"][(i, j_)] = x[i, j_].X

        result["z_hero"] = z_hero.X

        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X

        result["c_clear"] = c_.X

        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result
