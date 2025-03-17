# solver.py

import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m,            # 友方随从数量（已经在场上）
    n,            # 敌方随从数量
    h,            # 手牌中的随从/卡牌数量
    M,            # 本回合的法力水晶数量
    H_hero,       # 敌方英雄血量
    A, B,         # 友方随从（包括手牌召唤）对应的攻击力/生命值，共 m+h 个
    P, Q,         # 敌方随从的攻击力/生命值，共 n 个
    C, S,         # 手牌里每张卡的法力消耗/战略价值，共 h 个
    # 下列是权重，可以根据需求自行调节
    W1=10, W2=9, W6=8, W4=7, W3=6, W8=5, W5=4, W7=3
):
    """
    该函数基于用户提供的参数，使用 Gurobi 建模并求解“单回合决策”问题。
    包括以下关键逻辑：
      - c_ 用来表示是否成功“清场”（把敌方随从全部消灭）。
      - z_hero 表示敌方英雄的生存状况（0或1的含义视约定而定）。
      - 其余变量和约束对应之前 PDF/Markdown 里的“Full Model”。

    返回一个含有求解状态和各决策变量解的字典（若最优可行）。
    """

    # 创建模型
    model = gp.Model("NewOptimizationModel")

    # 1) 决策变量
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  
    # x_hero[i]表示第 i 个己方随从是否攻击敌方英雄

    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")        
    # z_hero 表示敌方英雄生存与否，或死亡/存活的二元状态

    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")         
    # x[i, j]表示己方随从 i 是否攻击敌方随从 j

    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")            
    # y[i] 表示己方随从 i 回合结束时是否存活

    z = model.addVars(n, vtype=GRB.BINARY, name="z")              
    # z[j] 表示敌方随从 j 是否存活

    u = model.addVars(h, vtype=GRB.BINARY, name="u")              
    # u[k] 表示手牌里第 k 张卡是否被打出/使用

    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")           
    # c_ 表示是否成功清理完所有敌方随从，即“清场”

    # 2) 目标函数（Objective）
    # 组合了 8 个部分的线性表达式
    objective = (
        # (1) + W1 * z_hero
        # 表示与敌方英雄存活（或死亡）相关的加权项
        W1 * z_hero
        # (2) + W2 * c_
        # 表示若成功清场（c_=1）则会获得的奖励
        + W2 * c_
        # (3) + W3 * sum(A[i] * x_hero[i])
        # 己方随从对英雄造成的伤害加成
        + W3 * gp.quicksum(A[i] * x_hero[i] for i in range(m+h))
        # (4) - W4 * sum(P[j] * z[j])
        # 留下高攻击敌方随从在场时的惩罚
        - W4 * gp.quicksum(P[j] * z[j] for j in range(n))
        # (5) + W5 * sum(B[i] * y[i])
        # 己方随从存活的收益
        + W5 * gp.quicksum(B[i] * y[i] for i in range(m+h))
        # (6) + W6 * sum(A[i] * x[i, j])
        # 己方随从对敌方随从造成伤害的奖励
        + W6 * gp.quicksum(A[i] * x[i, j] for i in range(m+h) for j in range(n))
        # (7) - W7 * sum(P[j] * x[i, j])
        # 己方随从在攻击时受到敌方反击伤害的惩罚
        - W7 * gp.quicksum(P[j] * x[i, j] for i in range(m+h) for j in range(n))
        # (8) + W8 * sum(S[k] * u[k])
        # 手牌中高价值卡牌打出的奖励
        + W8 * gp.quicksum(S[k] * u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

     # 3) Constraints

    # (A) Each minion can only attack once
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (B) Friendly minion survival
    for i in range(m):
        for j_ in range(n):
            model.addConstr(
                y[i] <= 1 - ((P[j_] - B[i] + 1) / max(P[j_], 1)) * x[i, j_],
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (C) Enemy minion survival
    for j_ in range(n):
        model.addConstr(
            z[j_] >= 1 - gp.quicksum((A[i] / max(Q[j_], 1)) * x[i, j_] for i in range(m+h)),
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (D) Enemy hero survival
    # If you want z_hero=1 => hero is "dead", you'll invert this constraint
    # but if it means "alive", keep as is, etc.
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
    for i in range(m, m + h):
        model.addConstr(
            y[i] <= u[i - m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (G) Mana constraint
    model.addConstr(
        gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (H) If a minion in hand isn't played, it can't attack
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

    # (I) Board clear constraints:
    # c_ <= 1 - z[j]  => if any z[j]=1 (an enemy minion survives), c_ forced to 0
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # Solve the model
    model.optimize()

    # 4) Gather solution
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
        # x_hero
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X
        # x(i,j)
        for i in range(m+h):
            for j_ in range(n):
                result["x_minions"][(i, j_)] = x[i, j_].X
        # z_hero
        result["z_hero"] = z_hero.X
        # z(j)
        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X
        # c_
        result["c_clear"] = c_.X
        # y(i) friendly minion survival
        for i in range(m+h):
            result["y_survive"][i] = y[i].X
        # u(k) => cards played
        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result
