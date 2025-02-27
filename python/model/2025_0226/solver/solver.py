# solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m, n, h,
    M,            # Mana
    H_hero,       # Enemy hero health
    A, B,         # Attack/Health for friendly + hand (size m+h)
    P, Q,         # Attack/Health for enemy (size n)
    C, S,         # Mana cost + strategic value (size h)
    W1=1, W2=1, W3=1, W4=1, W5=1, W6=1, W7=1
):
    """
    Sets up and solves the Gurobi model for a single turn based on your
    Full Model constraints and objective.

    Returns a dictionary with solution details if optimal.
    """

    # Create model
    model = gp.Model("NewOptimizationModel")

    # Decision variables
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")
    z = model.addVars(n, vtype=GRB.BINARY, name="z")
    u = model.addVars(h, vtype=GRB.BINARY, name="u")

    # Objective (from main.md or screenshot)
    objective = (
        W1 * z_hero
        + W2 * gp.quicksum(A[i] * x_hero[i] for i in range(m+h))
        - W3 * gp.quicksum(P[j] * z[j] for j in range(n))
        + W4 * gp.quicksum(B[i] * y[i] for i in range(m+h))
        + W5 * gp.quicksum(A[i] * x[i, j] for i in range(m+h) for j in range(n))
        - W6 * gp.quicksum(P[j] * x[i, j] for i in range(m+h) for j in range(n))
        + W7 * gp.quicksum(S[k] * u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # Constraints

    # 1) sum(x(i,j)) + x_hero(i) <= 1 (each minion can only attack once)
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # 2) y(i) <= 1 - sum_{j}((Pj - Bi + 1)/Pj * x(i,j))
    for i in range(m):
        for j in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j] - B[i] + 1) / max(P[j], 1)) * x[i, j],
                name=f"FriendlyMinionSurvival_{i}_{j}"
            )

    # 3) z(j) >= 1 - sum_{i}(Ai/Qj * x(i,j))
    for j in range(n):
        model.addConstr(
            z[j] >= 1 - gp.quicksum((A[i] / max(Q[j], 1)) * x[i, j] for i in range(m+h)),
            name=f"EnemyMinionSurvival_{j}"
        )

    # 4) z_hero >= 1 - sum_{i}(Ai/H_hero * x_hero(i))
    model.addConstr(
        z_hero >= 1 - gp.quicksum((A[i] / max(H_hero, 1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # 5) Board limit: sum(y_i) + sum(u_k) <= 7
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # 6) y(i) <= u(i-m) for i in [m..m+h], newly played minions must be played to survive
    for i in range(m, m + h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # 7) Mana constraint: sum(u_k * C_k) <= M
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # Link in-hand minions' attacks to whether they are played
    for i in range(m, m + h):
        model.addConstr(x_hero[i] <= u[i - m], f"HandMinionAttackHero_{i}")
        for j in range(n):
            model.addConstr(x[i, j] <= u[i - m], f"HandMinionAttackMinion_{i}_{j}")

    # (If you have charge/rush/taunt logic, add it here or adapt from main.md)

    # Solve
    model.optimize()

    # Gather solution
    result = {
        "status": model.status,
        "objective": None,
        "x_hero": {},
        "x_minions": {},
        "cards_played": {}
        # etc...
    }

    if model.status == GRB.OPTIMAL:
        result["objective"] = model.objVal
        # Example: store x_hero values
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X
        # store x(i,j)
        for i in range(m+h):
            for j in range(n):
                result["x_minions"][(i, j)] = x[i,j].X
        # store cards played
        for k in range(h):
            result["cards_played"][k] = u[k].X
        # etc...

    return result
