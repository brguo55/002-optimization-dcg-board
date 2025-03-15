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

    The objective function includes (by default):
      (1) + W1 * z_hero
      (2) + W2 * c            <-- single 'board-clear' bonus if all minions are dead
      (3) + W3 * sum_i(A[i] * x_hero[i])
      (4) - W4 * sum_j(P[j] * z[j])
      (5) + W5 * sum_i(B[i] * y[i])
      (6) + W6 * sum_{i,j}(A[i] * x[i,j])
      (7) - W7 * sum_{i,j}(P[j] * x[i,j])
      (8) + W8 * sum_{k}(S[k] * u[k])

    We use:
      c = 1 iff ALL enemy minions are dead, i.e. z[j] = 0 for all j.
      c <= 1 - z[j], for every j.

    Returns a dictionary of results.
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
    model = gp.Model("SingleTurn_BoardClear")

    # -----------------------------
    # 2) Decision variables
    # -----------------------------
    # (a) Attack on hero
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  
    # (b) Is enemy hero alive? (1=alive, 0=dead)
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")        
    # (c) Attack on enemy minions
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")         
    # (d) Does friendly minion survive?
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")            
    # (e) Does enemy minion j survive? (1=alive, 0=dead)
    z_ = model.addVars(n, vtype=GRB.BINARY, name="z")             
    # (f) Is card k played from hand?
    u = model.addVars(h, vtype=GRB.BINARY, name="u")              
    # (g) Single 'full board clear' variable
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")           

    # -----------------------------
    # 3) Objective function
    # -----------------------------
    objective = (
        # (1) + W1 * z_hero
        W1 * z_hero
        # (2) + W2 * c  (One-time bonus if c=1)
        + W2 * c_
        # (3) + W3 * sum_{i}(A[i] * x_hero[i])
        + W3 * gp.quicksum(A[i] * x_hero[i] for i in range(m+h))
        # (4) - W4 * sum_{j}(P[j] * z[j])
        - W4 * gp.quicksum(P[j] * z_[j] for j in range(n))
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
    # -----------------------------

    # (A) Each on-board minion i can attack at most once (enemy minion or hero)
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (B) Friendly minion survival constraints
    for i in range(m):
        for j in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j] - B[i] + 1) / max(P[j], 1)) * x[i, j],
                name=f"FriendlyMinionSurvival_{i}_{j}"
            )

    # (C) Enemy minion survival
    # if assigned damage < Qj => z[j] must be 1
    for j in range(n):
        model.addConstr(
            z_[j] >= 1 - gp.quicksum((A[i] / max(Q[j], 1)) * x[i, j] for i in range(m+h)),
            name=f"EnemyMinionSurvival_{j}"
        )

    # (D) Enemy hero survival
    model.addConstr(
        z_hero >= 1 - gp.quicksum((A[i] / max(H_hero, 1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (E) Board limit (cannot exceed 7 friendly minions after playing new ones)
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (F) If a “new” minion is not played, it can't survive
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

    # (H) If a minion in hand is not played, it can't attack
    for i in range(m, m+h):
        model.addConstr(
            x_hero[i] <= u[i - m],
            name=f"HandMinionAttackHero_{i}"
        )
        for j in range(n):
            model.addConstr(
                x[i, j] <= u[i - m],
                name=f"HandMinionAttackMinion_{i}_{j}"
            )

    # (I) Single board-clear variable:
    #     c <= 1 - z[j], so if any z[j]=1 (alive), c=0
    for j in range(n):
        model.addConstr(
            c_ <= 1 - z_[j],
            name=f"BoardClearConstraint_{j}"
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
        "c_clear": None
    }

    if model.status == GRB.OPTIMAL:
        result["objective"] = model.objVal

        # (a) x_hero
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        # (b) x(i,j)
        for i in range(m+h):
            for j in range(n):
                result["x_minions"][(i, j)] = x[i, j].X

        # (c) y(i)
        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        # (d) z_hero
        result["z_hero"] = z_hero.X

        # (e) z(j)
        for j in range(n):
            result["z_survive"][j] = z_[j].X

        # (f) c => single board-clear indicator
        result["c_clear"] = c_.X

        # (g) u(k)
        for k in range(h):
            result["u_cards"][k] = u[k].X

    return result

