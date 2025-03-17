# solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m,            # 已在场上的友方随从数量
    n,            # 敌方随从数量
    h,            # 手牌中可用随从/卡数量
    M,            # 本回合可用法力水晶数
    H_hero,       # 敌方英雄血量
    A, B,         # 友方随从(含手牌)的攻/血 (size = m+h)
    P, Q,         # 敌方随从的攻/血 (size = n)
    C, S,         # 手牌卡的法力消耗/战略值 (size = h)
    # 以下是各自权重，可根据需要微调
    W1=10, W2=9, W6=8, W4=7, W3=6, W8=5, W5=4, W7=3
):
    """
    基于输入参数构建并求解“单回合决策”模型。
    c_ 表示“清场”; z_hero 表示英雄(活/死)；z[j] 表示敌方随从是否存活。
    新增在(I')中增加“新召唤随从本回合无法攻击”的约束，忽略Charge/Rush。
    """

    # 创建模型
    model = gp.Model("NewOptimizationModel")

    # 1) 决策变量
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")        
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")         
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")            
    z = model.addVars(n, vtype=GRB.BINARY, name="z")              
    u = model.addVars(h, vtype=GRB.BINARY, name="u")              
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")           

    # 2) 目标函数 (Objective)
    objective = (
        # (1) + W1 * z_hero
        W1 * z_hero
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

    # 3) Constraints

    # (A) 每个己方随从只能攻击一次（要么打英雄、要么打一个随从、要么不攻击）
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (B) 友方随从生存：若攻击了足够强的敌方随从，可能死亡
    for i in range(m):
        for j_ in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j_] - B[i] + 1) / max(P[j_], 1)) * x[i, j_],
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (C) 敌方随从生存：如果对其造成足够伤害，则 z[j]可变为0
    for j_ in range(n):
        model.addConstr(
            z[j_] >= 1 - gp.quicksum((A[i] / max(Q[j_], 1)) * x[i, j_] for i in range(m+h)),
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (D) 敌方英雄生存：同理，如果累计伤害足够则 z_hero=0
    model.addConstr(
        z_hero >= 1 - gp.quicksum((A[i] / max(H_hero, 1)) * x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (E) Board limit: 当回合结束时，场上己方随从不能超过7个
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (F) 如要生存(y[i]=1)，则必须实际打出该手牌(u[i-m]=1)，对于新随从
    for i in range(m, m + h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (G) 法力约束：打出的手牌总法力花费不能超过 M
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (H) 未打出的牌不能攻击
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

    # (I') 新召唤随从当回合禁止攻击 (不考虑Charge/Rush)
    for i in range(m, m+h):
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i, j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # (I) 清场判定：若有任意 z[j]=1（仍存活），则 c_=0
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # 4) 开始求解
    model.optimize()

    # 5) 收集结果
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
