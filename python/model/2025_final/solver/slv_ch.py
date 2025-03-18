import gurobipy as gp
from gurobipy import GRB

def run_single_turn(
    m, n, h,
    M, H_hero,
    A, B, P, Q, C, S,
    weights=None,
    friendly_keywords=None,   # 对于每个友方随从 (索引 i in [0..m-1]) 的 'Keywords' 对象列表
    enemy_keywords=None       # 对于每个敌方随从 (索引 j in [0..n-1]) 的 'Keywords' 对象列表
):
    """
    一个只执行单回合的求解器，使用:
      - 每个随从的 'Keywords' 对象
      - 'Taunt' => 必须先杀掉所有带嘲讽的随从，才能攻击英雄或其他随从
      - 'Divine Shield' => 忽视一次致命伤害（简化模型）
      - 'Charge'/'Rush' => 目前仅占位（如果我们强制新随从不能攻击，则暂不使用）

    :param m: 场上友方随从数量
    :param n: 敌方随从数量
    :param h: 手牌中牌的数量
    :param M: 本回合可用的法力水晶数
    :param H_hero: 敌方英雄血量
    :param A,B: 对于 (m+h) 个友方随从的攻/血
    :param P,Q: 对于 n 个敌方随从的攻/血
    :param C,S: 对于手牌中 h 张牌的法力消耗和战略价值
    :param weights: 加权系数的字典 (W1..W8)。若为 None，则使用默认值。
    :param friendly_keywords: 长度为 m 的列表，每项是一个 'Keywords' 对象
    :param enemy_keywords: 长度为 n 的列表，每项是一个 'Keywords' 对象
    :return: 包含求解结果的字典
    """

    # 如果未提供 weights，则给出默认值
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

    # x_hero[i]: 二进制，表示友方随从 i 是否攻击英雄
    x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")

    # z_hero: 二进制，表示敌方英雄存活状态（1=存活，0=死亡）
    z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")

    # x[i,j]: 二进制，表示友方随从 i 是否攻击敌方随从 j
    x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")

    # y[i]: 二进制，表示友方随从 i 是否在战斗后依然存活
    y = model.addVars(m+h, vtype=GRB.BINARY, name="y")

    # z[j]: 二进制，表示敌方随从 j 是否存活
    z = model.addVars(n, vtype=GRB.BINARY, name="z")

    # u[k]: 二进制，表示手牌索引 k 的那张牌是否被打出
    u = model.addVars(h, vtype=GRB.BINARY, name="u")

    # c_: 二进制，表示是否清光了敌方随从（1=清场，0=否）
    c_ = model.addVar(vtype=GRB.BINARY, name="c_clear")

    # ds_f[i]: 二进制，表示友方随从 i 的圣盾是否已用掉 (1=用掉, 0=还在)
    ds_f = model.addVars(m, vtype=GRB.BINARY, name="ds_f")
    # ds_e[j]: 二进制，表示敌方随从 j 的圣盾是否已用掉 (1=用掉, 0=还在)
    ds_e = model.addVars(n, vtype=GRB.BINARY, name="ds_e")

    # 这里创建一个 Python 列表 hasTaunt，用于存储每个敌方随从 j 是否有嘲讽
    hasTaunt = []
    for j_ in range(n):
        hasTaunt.append(enemy_keywords[j_].has_keyword("Taunt"))

    # 4) 目标函数
    objective = (
        # W1*(1 - z_hero) => 击杀英雄的奖励
        W1 * (1 - z_hero)
        # W2*c_ => 清空敌方随从的奖励
        + W2 * c_
        # W3 => 打脸伤害
        + W3 * gp.quicksum(A[i]*x_hero[i] for i in range(m+h))
        # W4 => 留下敌方随从的惩罚（根据敌方随从攻击力做加权）
        - W4 * gp.quicksum(P[j]*z[j] for j in range(n))
        # W5 => 保持己方随从存活的奖励
        + W5 * gp.quicksum(B[i]*y[i] for i in range(m+h))
        # W6 => 对敌方随从造成伤害的奖励
        + W6 * gp.quicksum(A[i]*x[i,j] for i in range(m+h) for j in range(n))
        # W7 => 己方随从付出代价（受伤）的惩罚
        - W7 * gp.quicksum(P[j]*x[i,j] for i in range(m+h) for j in range(n))
        # W8 => 打出某些手牌的奖励
        + W8 * gp.quicksum(S[k]*u[k] for k in range(h))
    )
    model.setObjective(objective, GRB.MAXIMIZE)

    # 5) 约束条件

    # (1) 对于场上每个友方随从 i，只能攻击一次（要么打英雄，要么打一个随从，要么不攻击）
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i,j] for j in range(n)) + x_hero[i] <= 1,
            name=f"AttackConstraint_{i}"
        )

    # (2) 友方随从生存判断
    for i in range(m):
        for j_ in range(n):
            lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
            if lethal_factor < 0:
                lethal_factor = 0

            # 如果该友方随从带有“圣盾”，则第一次致命伤害忽略
            if friendly_keywords[i].has_keyword("Divine Shield"):
                ds_multiplier = 0
            else:
                ds_multiplier = 1

            model.addConstr(
                y[i] <= 1 - lethal_factor * x[i,j_] * ds_multiplier,
                name=f"FriendlyMinionSurvival_{i}_{j_}"
            )

    # (3) 敌方随从的生存判断
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i]/max(Q[j_], 1)) * x[i, j_] for i in range(m+h))
        # 如果该敌方随从带有“圣盾”，则忽略第一次致命伤害
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            ds_multiplier_e = 0
        else:
            ds_multiplier_e = 1

        model.addConstr(
            z[j_] <= 1 - damage_fraction * ds_multiplier_e,
            name=f"EnemyMinionSurvival_{j_}"
        )

    # (4) 清场 => c_=1 若所有敌方随从都死亡
    for j_ in range(n):
        model.addConstr(
            c_ <= 1 - z[j_],
            name=f"BoardClear_{j_}"
        )

    # (5) 敌方英雄的生存 => 如果打出足够斩杀伤害 => z_hero=0
    model.addConstr(
        z_hero <= 1 - gp.quicksum((A[i]/max(H_hero,1))*x_hero[i] for i in range(m+h)),
        name="EnemyHeroSurvival"
    )

    # (6) 友方随从数量限制 => 不能超过7个
    model.addConstr(
        gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
        name="BoardLimit"
    )

    # (7) 如果新打出的随从 i>=m 生存 => y[i]=1，则必须已打出 u[i-m]=1
    for i in range(m, m+h):
        model.addConstr(
            y[i] <= u[i-m],
            name=f"MinionPlayConstraint_{i}"
        )

    # (8) 法力水晶限制 => 打出的牌总消耗不能超过 M
    model.addConstr(
        gp.quicksum(u[k]*C[k] for k in range(h)) <= M,
        name="ManaConstraint"
    )

    # (9) 没有冲锋或突袭的随从当回合不能攻击；目前我们直接禁止新随从攻击
    for i in range(m, m+h):
        model.addConstr(x_hero[i] == 0, name=f"NoNewMinionHeroAttack_{i}")
        for j_ in range(n):
            model.addConstr(x[i,j_] == 0, name=f"NoNewMinionAttack_{i}_{j_}")

    # (10) 必须打出牌(u[i-m]=1)后才可攻击
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

    # --- TAUNT 相关约束 ---
    # 若有随从具有Taunt且存活，则禁止攻击英雄
    for i in range(m):
        model.addConstr(
            x_hero[i] <= 1 - gp.quicksum(z[j_] for j_ in range(n) if hasTaunt[j_]),
            name=f"NoHeroIfTaunt_{i}"
        )

    # 若有嘲讽随从存活，则禁止攻击那些没有嘲讽的随从
    for i in range(m):
        for j_ in range(n):
            if not hasTaunt[j_]:
                model.addConstr(
                    x[i,j_] <= 1 - gp.quicksum(z[k] for k in range(n) if hasTaunt[k]),
                    name=f"MustKillTauntFirst_{i}_{j_}"
                )

    # 2) “翻转”约束 (flip constraints) 用于友方随从：
    #    如果带圣盾的友方随从 i 被任一敌方随从攻击，则 ds_f[i] 必须=1（表示圣盾用掉）
    for i in range(m):
        if friendly_keywords[i].has_keyword("Divine Shield"):
            model.addConstr(
                ds_f[i] >= gp.quicksum(x[i,j] for j in range(n)),
                name=f"FlipFriendlyShield_{i}"
            )
        else:
            model.addConstr(ds_f[i] == 1, name=f"NoFriendlyDS_{i}")

    # 3) “翻转”约束 (flip constraints) 用于敌方随从：
    #    如果带圣盾的敌方随从 j 被任一友方随从 i 攻击，则 ds_e[j] = 1
    for j_ in range(n):
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            model.addConstr(
                ds_e[j_] >= gp.quicksum(x[i,j_] for i in range(m+h)),
                name=f"FlipEnemyShield_{j_}"
            )
        else:
            model.addConstr(ds_e[j_] == 1, name=f"NoEnemyDS_{j_}")

    # 4) 友方随从若带圣盾，在 ds_f[i]=0 时忽略致命伤害；=1 时则正常结算
    for i in range(m):
        if friendly_keywords[i].has_keyword("Divine Shield"):
            for j_ in range(n):
                lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
                if lethal_factor < 0:
                    lethal_factor = 0
                # ds_f[i] = 0 => 无法被致命伤害击杀
                # ds_f[i] = 1 => 正常结算
                model.addConstr(
                    y[i] <= 1 - lethal_factor * x[i,j_] * ds_f[i],
                    name=f"DS_FriendlySurvival_{i}_{j_}"
                )
        else:
            # 若无圣盾，则直接使用普通的致命伤害公式
            for j_ in range(n):
                lethal_factor = (P[j_] - B[i] + 1) / max(P[j_], 1)
                if lethal_factor < 0:
                    lethal_factor = 0
                model.addConstr(
                    y[i] <= 1 - lethal_factor * x[i,j_],
                    name=f"NormalFriendlySurvival_{i}_{j_}"
                )

    # 5) 敌方随从如果带圣盾，也是同理
    for j_ in range(n):
        damage_fraction = gp.quicksum((A[i] / max(Q[j_],1)) * x[i,j_] for i in range(m+h))
        if enemy_keywords[j_].has_keyword("Divine Shield"):
            model.addConstr(
                z[j_] <= 1 - damage_fraction * ds_e[j_],
                name=f"DS_EnemySurvival_{j_}"
            )
        else:
            model.addConstr(
                z[j_] <= 1 - damage_fraction,
                name=f"NormalEnemySurvival_{j_}"
            )

    # 6) 开始求解
    model.optimize()

    # 7) 收集结果
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

        # 英雄攻击输出
        for i in range(m+h):
            result["x_hero"][i] = x_hero[i].X

        # 随从之间的攻击
        for i in range(m+h):
            for j_ in range(n):
                result["x_minions"][(i, j_)] = x[i, j_].X

        # 英雄存活状态
        result["z_hero"] = z_hero.X

        # 敌方随从存活状态
        for j_ in range(n):
            result["z_enemy"][j_] = z[j_].X

        # 是否清场
        result["c_clear"] = c_.X

        # 哪些友方随从存活
        for i in range(m+h):
            result["y_survive"][i] = y[i].X

        # 哪些牌被打出
        for k in range(h):
            result["cards_played"][k] = u[k].X

    return result
