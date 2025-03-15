import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    scenario_data, 
    # w1 > w2 > w6 > w4 > w3 > w8 > w5 > w7 by default:
    W1=10,  # highest
    W2=9,
    W6=8,
    W4=7,
    W3=6,
    W8=5,
    W5=4,
    W7=3,
):
    """
    Builds and solves a single-turn Gurobi model using a single dictionary 'scenario_data'
    that must contain these keys:
      scenario_data = {
          "m": m,
          "n": n,
          "h": h,
          "M": M,
          "H_hero": H_hero,
          "A": A,   # Attack array (size m+h)
          "B": B,   # Health array (size m+h)
          "P": P,   # Enemy minion attacks (size n)
          "Q": Q,   # Enemy minion health  (size n)
          "C": C,   # Mana cost for hand   (size h)
          "S": S    # Strat value for hand (size h)
      }

    The objective function includes:
      1) + W1 * z_hero
      2) + W2 * sum_{j}(P[j] * c[j])
      3) + W3 * sum_{i}(A[i] * x_hero[i])
      4) - W4 * sum_{j}(P[j] * z[j])
      5) + W5 * sum_{i}(B[i] * y[i])
      6) + W6 * sum_{i,j}(A[i] * x[i,j])
      7) - W7 * sum_{i,j}(P[j] * x[i,j])
      8) + W8 * sum_{k}(S[k] * u[k])

    Also defines c[j] (binary) to indicate if enemy minion j is 'cleared.'

    Returns a dictionary of results, or partial info if not optimal.
    """

    # -----------------------------
    # 1) Unpack scenario_data
    # -----------------------------
    m = scenario_data["m"]             # #friendly minions on board
    n = scenario_data["n"]             # #enemy minions
    h = scenario_data["h"]             # #cards in hand
    M = scenario_data["M"]             # mana
    H_hero = scenario_data["H_hero"]   # enemy hero health
    A = scenario_data["A"]             # friendly attack array
    B = scenario_data["B"]             # friendly health array
    P = scenario_data["P"]             # enemy minion attack array
    Q = scenario_data["Q"]             # enemy minion health array
    C = scenario_data["C"]             # mana cost for each card in hand
    S = scenario_data["S"]             # strat value for each card in hand

    # Create model
    model = gp.Model("SingleTurn_NewObjective")

    # -----------------------------
    # 2) Decision variables
    # -----------------------------
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")   # minion i => hero
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")         # enemy hero dead?
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")          # minion i => enemy minion j
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")             # does friendly minion i survive?
    z = model.addVars(n, vtype=GRB.BINARY, name="z")               # does enemy minion j survive?
    u = model.addVars(h, vtype=GRB.BINARY, name="u")               # is card k played from hand?
    c = model.addVars(n, vtype=GRB.BINARY, name="c")               # cleared (killed) enemy minion j?

    # -----------------------------
    # 3) Objective function (eight terms)
    #    We combine them with + or -
    # -----------------------------
    objective = (
        # (1) + W1 * z_hero
        W1 * z_hero
        # (2) + W2 * sum_{j}(P[j] * c[j])
        + W2 * gp.quicksum(P[j] * c[j] for j in range(n))
        # (3) + W3 * sum_{i}(A[i] * x_hero[i])
        + W3 * gp.quicksum(A[i] * x_hero[i] for i in range(m+h))
        # (4) - W4 * sum_{j}(P[j] * z[j])
        - W4 * gp.quicksum(P[j] * z[j] for j in range(n))
        # (5) + W5 * sum_{i}(B[i] * y[i])
        + W5 * gp.quicksum(B[i] * y[i] for i in range(m+h))
        # (6) + W6 * sum_{i,j}(A[i] * x[i,j])
        + W6 * gp.quicksum(A[i] * x[i, j] for i in range(m+h) for j in range(n))
        # (7) - W7 * sum_{i,j}(P[j] * x[i,j])
        - W7 * gp.quicksum(P[j] * x[i, j] for i in range(m+h) for j in range(n))
        # (8) + W8 * sum_{k}(S[k] * u[k])
        + W8 * gp.quicksum(S[k] * u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # -----------------------------
    # 4) Constraints
    # (We copy from your original code, plus c_j constraint)
    # -----------------------------

    # (A) Each friendly minion i can attack at most once
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (B) Friendly minion survival
    for i in range(m):
        for j in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j] - B[i] + 1) / max(P[j], 1)) * x[i, j],
                name=f"FriendlyMinionSurvival_{i}_{j}"
            )

    # (C) Enemy minion survival
    for j in range(n):
        model.addConstr(
            z[j] >= 1 - gp.quicksum((A[i] / max(Q[j], 1)) * x[i, j] for i in range(m+h)),
            name=f"EnemyMinionSurvival_{j}"
        )

    # (D) Enemy hero survival
    model.addConstr(
        z_hero >= 1 - gp.quicksum((A[i] / max(H_hero, 1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (E) Board limit
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (F) Newly played minions must be played to survive
    for i in range(m, m+h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (G) Mana constraint
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # Link in-hand minion's attacks to whether they are played
    for i in range(m, m+h):
        model.addConstr(x_hero[i] <= u[i-m], name=f"HandMinionAttackHero_{i}")
        for j in range(n):
            model.addConstr(x[i, j] <= u[i-m], name=f"HandMinionAttackMinion_{i}_{j}")

    # (H) c_j constraint: If total assigned damage >= Q[j], c[j] can be forced to 1
    for j in range(n):
        model.addConstr(
            c[j] >= 1 - gp.quicksum((A[i]/max(Q[j], 1)) * x[i, j] for i in range(m+h)),
            name=f"ClearedMinion_{j}"
        )

    # -----------------------------
    # 5) Solve the model
    # -----------------------------
    model.optimize()

    # -----------------------------
    # 6) Collect results
    # -----------------------------
    result = {
        "status": model.status,
        "objective": None,
        "x_hero": {},
        "x_minions": {},
        "y_survive": {},
        "z_hero": None,
        "z_survive": {},
        "u_cards": {},
        "c_clear": {}
    }

    if model.status == GRB.OPTIMAL:
        result["objective"] = model.objVal

        # x_hero
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        # x(i,j)
        for i in range(m+h):
            for j in range(n):
                result["x_minions"][(i,j)] = x[i,j].X

        # y(i)
        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        # z_hero
        result["z_hero"] = z_hero.X

        # z(j)
        for j in range(n):
            result["z_survive"][j] = z[j].X

        # c(j)
        for j in range(n):
            result["c_clear"][j] = c[j].X

        # u(k)
        for k in range(h):
            result["u_cards"][k] = u[k].X

    return result

