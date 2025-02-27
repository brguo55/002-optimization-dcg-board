# turn_solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m, n, h, M, H_hero,
    A, B, P, Q, C, S,
    # references to game state (optional)
    W1=1, W2=1, W3=1, W4=1, W5=1, W6=1, W7=1
):
    """
    Sets up and solves the Full Model for a single turn, given:
      - m: Number of friendly minions on the battlefield
      - n: Number of enemy minions
      - h: Number of cards in hand
      - M: Available mana
      - H_hero: Enemy hero's health
      - A: Attack of friendly minions (size m+h)
      - B: Health of friendly minions (size m+h)
      - P: Attack of enemy minions (size n)
      - Q: Health of enemy minions (size n)
      - C: Mana cost for in-hand cards (size h)
      - S: Strategic value for in-hand cards (size h)
      - W1..W7: Weights from your model

    Returns a dict with solution details (if optimal).
    """

    # Create model
    model = gp.Model("FullModelTurn")

    # Decision Variables
    # x(i,hero): whether friendly minion i attacks the enemy hero
    x_hero = model.addVars(m + h, vtype=GRB.BINARY, name="x_hero")

    # z_hero: whether the enemy hero dies (1 if dead, 0 if survives)
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")

    # x(i,j): whether friendly minion i attacks enemy minion j
    x = model.addVars(m + h, n, vtype=GRB.BINARY, name="x")

    # y(i): whether friendly minion i survives (1 if survives, 0 if dies)
    y = model.addVars(m + h, vtype=GRB.BINARY, name="y")

    # z(j): whether enemy minion j dies (1 if dead, 0 if survives)
    z = model.addVars(n, vtype=GRB.BINARY, name="z")

    # u(k): whether card k in hand is played
    u = model.addVars(h, vtype=GRB.BINARY, name="u")

    # Objective Function (from your screenshot)
    # Maximize: W1*z_hero + W2 * sum(Ai*x(i,hero)) - W3 * sum(Pj*zj)
    #           + W4*sum(Bi*yi) + W5*sum(Ai*x(i,j)) - W6*sum(Pj*x(i,j))
    #           + W7*sum(S_{m+k}*u_{m+k})  (or sum of S[k]*u[k] if we map carefully)
    objective = (
        W1 * z_hero
        + W2 * gp.quicksum(A[i] * x_hero[i] for i in range(m + h))
        - W3 * gp.quicksum(P[j] * z[j] for j in range(n))
        + W4 * gp.quicksum(B[i] * y[i] for i in range(m + h))
        + W5 * gp.quicksum(A[i] * x[i, j] for i in range(m + h) for j in range(n))
        - W6 * gp.quicksum(P[j] * x[i, j] for i in range(m + h) for j in range(n))
        + W7 * gp.quicksum(S[k] * u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # Constraints (from your screenshot)

    # 1) sum_{j=1..n} x(i,j) + x(i,hero) <= 1, for i in 1..m
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # 2) y(i) <= 1 - sum_{j=1..n} [ (Pj - Bi + 1)/Pj * x(i,j) ], for i in 1..m
    #    This ensures friendly minion i survives only if it can withstand the enemy minion's counterattack
    for i in range(m):
        model.addConstr(
            y[i] <= 1 - gp.quicksum(
                ((P[j] - B[i] + 1) / max(P[j], 1)) * x[i, j] for j in range(n)
            ),
            name=f"FriendlyMinionSurvival_{i}"
        )

    # 3) z(j) >= 1 - sum_{i=1..m+h} [ Ai / Qj * x(i,j) ], for j in 1..n
    for j in range(n):
        model.addConstr(
            z[j] >= 1 - gp.quicksum(
                (A[i] / max(Q[j], 1)) * x[i, j] for i in range(m + h)
            ),
            name=f"EnemyMinionSurvival_{j}"
        )

    # 4) z_hero >= 1 - sum_{i=1..m+h} [ Ai / H_hero * x_hero(i) ]
    model.addConstr(
        z_hero >= 1 - gp.quicksum((A[i] / max(H_hero, 1)) * x_hero[i] for i in range(m + h)),
        name="EnemyHeroSurvival"
    )

    # 5) sum_{i=1..m} y(i) + sum_{i=m+1..m+h} u(i) <= 7  (board limit)
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # 6) y(i) <= u(i), for i in m+1..m+h (newly played minions must be played to survive)
    for i in range(m, m + h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # 7) sum_{k=1..h} [ u(k) * C(k) ] <= M (mana constraint)
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # Solve
    model.optimize()

    # Gather results
    solution = {
        "status": model.status,
        "objective": None if model.status != GRB.OPTIMAL else model.objVal,
        "x_hero": {},
        "x_minions": {},
        "y_survive": {},
        "z_dead": {},
        "z_hero_dead": None,
        "cards_played": {}
    }

    if model.status == GRB.OPTIMAL:
        solution["objective"] = model.objVal
        # Extract x_hero
        for i in range(m + h):
            solution["x_hero"][i] = x_hero[i].X

        # Extract x(i,j)
        for i in range(m + h):
            for j in range(n):
                solution["x_minions"][(i, j)] = x[i, j].X

        # Extract y(i), z(j), z_hero, u(k)
        for i in range(m + h):
            solution["y_survive"][i] = y[i].X
        for j in range(n):
            solution["z_dead"][j] = z[j].X
        solution["z_hero_dead"] = z_hero.X
        for k in range(h):
            solution["cards_played"][k] = u[k].X

    return solution
