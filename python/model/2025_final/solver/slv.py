# solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m, n, h,
    M, H_hero,
    A, B, P, Q, C, S,
    weights=None,
    friendly_keywords=None,   # list of 'Keywords' objects for each friendly minion i in [0..m-1]
    enemy_keywords=None       # list of 'Keywords' objects for each enemy minion j in [0..n-1]
):
    """
    A single-turn solver that uses:
      - 'Keywords' objects for each minion
      - 'Taunt' => must kill all taunt minions before attacking hero or non-taunt minions
      - 'Divine Shield' => ignore lethal damage once (simple model)
      - 'Charge'/'Rush' => placeholders (not used if we forcibly block new minion attacks)

    :param m: Number of friendly minions on board
    :param n: Number of enemy minions on board
    :param h: Number of cards in hand
    :param M: Mana available
    :param H_hero: Enemy hero health
    :param A,B: Attack/Health for m+h friendly minions
    :param P,Q: Attack/Health for n enemy minions
    :param C,S: Mana cost & strategic values for h cards
    :param weights: Dict of weighting factors (W1..W8). If None, defaults used.
    :param friendly_keywords: list of length m, each item a 'Keywords' object
    :param enemy_keywords:    list of length n, each item a 'Keywords' object
    :return: A dictionary with solver results
    """

    if weights is None:
        weights = {
            "W1": 1,
            "W2": 1,
            "W3": 1,
            "W4": 1,
            "W5": 1,
            "W6": 1,
            "W7": 1,
            "W8": 1
        }

    W1 = weights["W1"]
    W2 = weights["W2"]
    W3 = weights["W3"]
    W4 = weights["W4"]
    W5 = weights["W5"]
    W6 = weights["W6"]
    W7 = weights["W7"]
    W8 = weights["W8"]

    from classes.keywords import Keywords
    if friendly_keywords is None:
        friendly_keywords = [Keywords([], "Neutral") for _ in range(m)]
    if enemy_keywords is None:
        enemy_keywords = [Keywords([], "Neutral") for _ in range(n)]

    model = gp.Model("KeywordSolverModel")

    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  # minion i attacks hero
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")       # 1=hero alive, 0=dead
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")        # minion i attacks minion j
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")           # friendly minion i alive
    z = model.addVars(n, vtype=GRB.BINARY, name="z")             # enemy minion j alive
    u = model.addVars(h, vtype=GRB.BINARY, name="u")             # card k is played
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")          # board clear
    # (Assuming you’re inside run_single_turn, after creating the model)
    ds_f = model.addVars(m, vtype=GRB.BINARY, name="ds_f")
    ds_e = model.addVars(n, vtype=GRB.BINARY, name="ds_e")
    
    hasTaunt = []
    for j_ in range(n):
        hasTaunt.append( enemy_keywords[j_].has_keyword("Taunt") )



    # 4) Objective
    objective = (
        # W1*(1 - z_hero) => reward killing hero
        W1 * (1 - z_hero)
        # W2*c_ => reward board clear
        + W2 * c_
        # W3 => face damage
        + W3 * gp.quicksum(A[i]*x_hero[i] for i in range(m+h))
        # W4 => penalty for leaving enemy minions alive
        - W4 * gp.quicksum(P[j]*z[j] for j in range(n))
        # W5 => reward for friendly minion survival
        + W5 * gp.quicksum(B[i]*y[i] for i in range(m+h))
        # W6 => reward for minion->minion damage
        + W6 * gp.quicksum(A[i]*x[i,j] for i in range(m+h) for j in range(n))
        # W7 => penalty for your minions taking damage
        - W7 * gp.quicksum(P[j]*x[i,j] for i in range(m+h) for j in range(n))
        # W8 => reward for playing cards
        + W8 * gp.quicksum(S[k]*u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # 5) Constraints

    # (1) Each on-board friendly minion can only attack once
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i,j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (2) Friendly minion survival
    for i in range(m):
        for j_ in range(n):
            lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
            if lethal_factor < 0:
                lethal_factor = 0

            # If this friendly minion i has Divine Shield => ignore lethal once
            if friendly_keywords[i].has_keyword("Divine Shield"):
                ds_multiplier = 0
            else:
                ds_multiplier = 1

            model.addConstr(
                y[i] <= 1 - lethal_factor * x[i,j_] * ds_multiplier,
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (3) Enemy minion survival
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i]/max(Q[j_], 1)) * x[i, j_] for i in range(m+h))
        # If enemy j_ has "Divine Shield", ignore lethal
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            ds_multiplier_e = 0
        else:
            ds_multiplier_e = 1

        model.addConstr(
            z[j_] <= 1 - damage_fraction * ds_multiplier_e,
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (4) Board clear => c_=1 iff all enemy minions are dead
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # (5) Enemy hero survival => if enough fraction => hero is dead
    model.addConstr(
        z_hero <= 1 - gp.quicksum((A[i]/max(H_hero,1))*x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (6) Board limit => at most 7 total friendly minions
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (7) If a newly played minion i>=m survived => must have been played => u[i-m]
    for i in range(m, m+h):
        model.addConstr(
            y[i] <= u[i-m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (8) Mana limit => sum of played cards <= M
    model.addConstr(
        gp.quicksum(u[k]*C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (9) Newly summoned minions can't attack if they don't have "Charge"/"Rush"
    # For now, we skip them attacking entirely
    for i in range(m, m+h):
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i,j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # (10) Must be played to attack
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

    # --- TAUNT Constraints ---
    # Forbid hero attacks if any minion with Taunt is alive
    for i in range(m):
        model.addConstr(
            x_hero[i] <= 1 - gp.quicksum(z[j_] for j_ in range(n) if hasTaunt[j_]),
            name=f"NoHeroIfTaunt_{i}"
        )

    # Forbid attacking minions that do NOT have taunt while any taunt is alive
    for i in range(m):
        for j_ in range(n):
            if not hasTaunt[j_]:
                model.addConstr(
                    x[i,j_] <= 1 - gp.quicksum(z[k] for k in range(n) if hasTaunt[k]),
                    name=f"MustKillTauntFirst_{i}_{j_}"
                )

            
    # 2) "Flip" constraints for friendly minions:
    #    If a friendly minion i with DS is attacked by any enemy j,
    #    then ds_f[i] must be 1 (shield removed).
    for i in range(m):
        if friendly_keywords[i].has_keyword("Divine Shield"):
            # If x[i,j] = 1 for any j, then ds_f[i] >= 1
            model.addConstr(
                ds_f[i] >= gp.quicksum(x[i,j] for j in range(n)),
                name=f"FlipFriendlyShield_{i}"
            )
        else:
            # If no DS, set ds_f[i] = 1 from the start (shield is effectively "gone")
            model.addConstr(ds_f[i] == 1, name=f"NoFriendlyDS_{i}")

    # 3) "Flip" constraints for enemy minions:
    #    If an enemy minion j with DS is attacked by any friendly minion i,
    #    then ds_e[j] must be 1 (shield removed).
    for j_ in range(n):
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            model.addConstr(
                ds_e[j_] >= gp.quicksum(x[i,j_] for i in range(m+h)),
                name=f"FlipEnemyShield_{j_}"
            )
        else:
            model.addConstr(ds_e[j_] == 1, name=f"NoEnemyDS_{j_}")

    # 4) Survival constraints for friendly minions with DS
    #    If ds_f[i] = 0 => ignore lethal for the first attack
    #    If ds_f[i] = 1 => apply normal lethal check
    for i in range(m):
        # We'll do the same loop over j_ in [0..n-1]
        # If a minion doesn't have DS, we handle it with normal lethal below
        if friendly_keywords[i].has_keyword("Divine Shield"):
            for j_ in range(n):
                lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
                if lethal_factor < 0:
                    lethal_factor = 0
                # If ds_f[i] = 0, lethal is multiplied by 0 => no kill
                # If ds_f[i] = 1, normal lethal applies
                model.addConstr(
                    y[i] <= 1 - lethal_factor * x[i,j_] * ds_f[i],
                    name=f"DS_FriendlySurvival_{i}_{j_}"
                )
        else:
            # No DS => normal lethal
            for j_ in range(n):
                lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
                if lethal_factor < 0:
                    lethal_factor = 0
                model.addConstr(
                    y[i] <= 1 - lethal_factor * x[i,j_],
                    name=f"NormalFriendlySurvival_{i}_{j_}"
                )

    # 5) Survival constraints for enemy minions with DS
    #    Similar logic: if ds_e[j_] = 0 => they can't be killed by the first attack,
    #    if ds_e[j_] = 1 => normal lethal fraction
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i] / max(Q[j_],1)) * x[i,j_] for i in range(m+h))
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            model.addConstr(
                z[j_] <= 1 - damage_fraction * ds_e[j_],
                name=f"DS_EnemySurvival_{j_}"
            )
        else:
            # normal lethal
            model.addConstr(
                z[j_] <= 1 - damage_fraction,
                name=f"NormalEnemySurvival_{j_}"
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

        # Extract hero attacks
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        # Extract minion attacks
        for i in range(m+h):
            for j_ in range(n):
                result["x_minions"][(i, j_)] = x[i, j_].X

        # Hero alive/dead
        result["z_hero"] = z_hero.X

        # Enemy minions alive/dead
        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X

        # Board clear
        result["c_clear"] = c_.X

        # Which friendly minions survived
        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        # Which cards were played
        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result
