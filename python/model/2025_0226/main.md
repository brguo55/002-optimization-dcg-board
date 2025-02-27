## Gurobi Model 2025/01/28

### 01: Preparation Phase (Package Loading & Import)


```python
from typing import List
import gurobipy as gp
from gurobipy import GRB

# Initialize Gurobi model
model = gp.Model("Gameplay_Optimization")
```

    Restricted license - for non-production use only - expires 2026-11-23



```python
from classes.keywords import Keywords
from classes.minion import Minion
```


```python
from scenarios.basic_example import friendly_minions, enemy_minions, hand_list
from scenarios.deck_example import deck_15, add_card_to_hand
```


```python
print("Initial deck size:", len(deck_15))
print("Initial hand_example list:", len(hand_list))

# Draw one random card from deck_15, add it to hand_example
drawn_card = add_card_to_hand(deck_15, hand_list)
print("Drew card:", drawn_card)
print("Deck size after draw:", len(deck_15))
print("Hand list size after draw:", len(hand_list))
```

    Initial deck size: 15
    Initial hand_example list: 3
    Drew card: Minion: Amani Berserker | Class: Neutral | Attack: 2 | Health: 3 | Keywords: 
    Deck size after draw: 14
    Hand list size after draw: 4


### 02: Preparation Phase


```python
# Number of minions
m = len(friendly_minions)  # Number of friendly minions
n = len(enemy_minions)     # Number of enemy minions
h = len(hand_list)  # Number of cards in hand 
M = 5  # Available mana for the current turn (e.g., turn 5)
H_hero = 12 # Enemy hero's health is set to 18

# Combine friendly_minions + hand into a single list if you want to treat them similarly
combined_minions = friendly_minions + hand_list

A = [minion.attack for minion in combined_minions]  # Friendly minion attack values
B = [minion.health for minion in combined_minions]  # Friendly minion health values
P = [minion.attack for minion in enemy_minions]     # Enemy minion attack values
Q = [minion.health for minion in enemy_minions]     # Enemy minion health values

# Strategic values and mana costs
S = [minion.strat_value for minion in hand_list]
C = [minion.mana_cost for minion in hand_list]

# Weights (example values, you can modify as needed)
W_1 = 1
W_2 = 1
W_3 = 1
W_4 = 1
W_5 = 1
W_6 = 1
W_7 = 1
```

### 03: Gurobi Modeling Phase


```python
import gurobipy as gp
from gurobipy import GRB

model = gp.Model("NewOptimizationModel")

# Decision variables
x_hero = model.addVars(m+h, vtype=GRB.BINARY, name="x_hero")  # Whether minion i attacks hero
z_hero = model.addVar(vtype=GRB.BINARY, name="z_hero")        # Whether the enemy hero survives
x = model.addVars(m+h, n, vtype=GRB.BINARY, name="x")         # Whether minion i attacks enemy minion j
y = model.addVars(m+h, vtype=GRB.BINARY, name="y")            # Whether friendly minion i survives
z = model.addVars(n, vtype=GRB.BINARY, name="z")              # Whether enemy minion j survives
u = model.addVars(h, vtype=GRB.BINARY, name="u")              # Whether card k is played (k in 0..h-1)

# Objective function
# Define the objective function
objective = (
    W_1 * z_hero  # Term for enemy hero survival
    + W_2 * gp.quicksum(x_hero[i] * A[i] for i in range(m+h))  # Damage to enemy hero
    - W_3 * gp.quicksum(z[j] * P[j] for j in range(n))  # Minimize enemy minion survival
    + W_4 * gp.quicksum(y[i] * B[i] for i in range(m+h))  # Preserve friendly minion health
    + W_5 * gp.quicksum(A[i] * x[i, j] for i in range(m+h) for j in range(n))  # Damage to enemy minions
    - W_6 * gp.quicksum(P[j] * x[i, j] for i in range(m+h) for j in range(n))  # Penalize damage to friendly minions
    + W_7 * gp.quicksum(S[k] * u[k] for k in range(h))  # Strategic value of played cards
)

# Set the objective function in Gurobi
model.setObjective(objective, gp.GRB.MAXIMIZE)


model.setObjective(objective, GRB.MAXIMIZE)

# Hero attack constraint (each minion attacks at most once)
for i in range(m):
    model.addConstr(
        gp.quicksum(x[i, j] for j in range(n)) + x_hero[i] <= 1,
        f"AttackConstraint_{i}"
    )

# Friendly minion survival constraint
for i in range(m):
    for j in range(n):
        model.addConstr(
            y[i] <= 1 - ((P[j] - B[i] + 1) / max(P[j], 1)) * x[i, j],
            f"FriendlyMinionSurvival_{i}_{j}"
        )

# Enemy minion survival constraint
for j in range(n):
    model.addConstr(
        z[j] >= 1 - gp.quicksum((A[i] / Q[j]) * x[i, j] for i in range(m+h)),
        f"EnemyMinionSurvival_{j}"
    )

# Enemy hero survival constraint
model.addConstr(
    z_hero >= 1 - gp.quicksum((A[i] / H_hero) * x_hero[i] for i in range(m+h)),
    "EnemyHeroSurvival"
)

# Maximum number of minions on board constraint (7 minions max)
model.addConstr(
    gp.quicksum(y[i] for i in range(m)) + gp.quicksum(u[k] for k in range(h)) <= 7,
    "BoardLimit"
)

# Newly played minions must be played before surviving (yi ≤ ui)
for i in range(m, m+h):
    model.addConstr(
        y[i] <= u[i-m],
        f"MinionPlayConstraint_{i}"
    )

# Mana constraint
model.addConstr(
    gp.quicksum(u[k] * C[k] for k in range(h)) <= M,
    "ManaConstraint"
)

# Link in-hand minions' attacks to whether they are played
for i in range(m, m+h):
    # If the minion is not played, it cannot attack
    model.addConstr(x_hero[i] <= u[i-m], f"HandMinionAttackHero_{i}")
    for j in range(n):
        model.addConstr(x[i, j] <= u[i-m], f"HandMinionAttackMinion_{i}_{j}")

# Charge/Rush logic
for i in range(m, m+h):
    minion = hand_list[i-m]
    has_charge = minion.keywords.has_keyword("Charge")
    has_rush = minion.keywords.has_keyword("Rush")

    if not has_charge and not has_rush:
        # No Charge/Rush: can't attack at all this turn
        model.addConstr(x_hero[i] == 0, f"NoChargeRushHero_{i}")
        for j in range(n):
            model.addConstr(x[i, j] == 0, f"NoChargeRushMinion_{i}_{j}")
    elif has_rush and not has_charge:
        # Rush: can attack minions but not hero
        model.addConstr(x_hero[i] == 0, f"RushNoHero_{i}")
        # No further constraints needed since we already have u[i-m] controlling play
    elif has_charge:
        # Charge: can attack hero or minions if played
        # No additional constraints needed
        pass

# Taunt logic
tt = [1 if enemy_minion.keywords.has_keyword("Taunt") else 0 for enemy_minion in enemy_minions]
taunt_present = model.addVar(vtype=GRB.BINARY, name="taunt_present")

# If any taunt minion is alive, taunt_present = 1
for j in range(n):
    model.addConstr(taunt_present >= tt[j] * z[j], f"TauntPresentLower_{j}")

model.addConstr(
    taunt_present <= gp.quicksum(tt[j] * z[j] for j in range(n)),
    "TauntPresentUpper"
)

# If Taunt is present, no attacks on the hero
for i in range(m+h):
    model.addConstr(
        x_hero[i] <= 1 - taunt_present,
        f"RestrictHeroAttack_{i}"
    )

# Prioritize attacking Taunt minions if they exist
for i in range(m+h):
    model.addConstr(
        gp.quicksum(x[i, j] * (1 - tt[j]) for j in range(n))
        <= gp.quicksum(x[i, j] * tt[j] for j in range(n)) + (1 - taunt_present),
        f"PrioritizeTaunt_{i}"
    )

# Divine Shield handling
ds_active = model.addVars(n, vtype=GRB.BINARY, name="ds_active")

for j, enemy_minion in enumerate(enemy_minions):
    if enemy_minion.keywords.has_keyword("Divine Shield"):
        model.addConstr(
            ds_active[j] + gp.quicksum(x[i, j] for i in range(m+h)) <= 1,
            f"DivineShieldBreak_{j}"
        )
    else:
        model.addConstr(ds_active[j] == 0, f"NoDivineShield_{j}")

# Solve the model
model.optimize()

# Display results
if model.status == GRB.OPTIMAL:
    print("Optimal objective value:", model.objVal)
    print("Enemy minions survival (z):")
    for j in range(n):
        print(f"z[{j}] = {z[j].X}")

    print("Friendly minions attacking enemy minions (x):")
    for i in range(m+h):
        for j in range(n):
            print(f"x[{i},{j}] = {x[i, j].X}")

    print("Friendly minions survival (y):")
    for i in range(m+h):
        print(f"y[{i}] = {y[i].X}")

    print("Cards played (u):")
    for k in range(h):
        print(f"u[{k}] = {u[k].X}")

    print("Taunt present:", taunt_present.X)
    for j in range(n):
        print(f"ds_active[{j}] = {ds_active[j].X}")
else:
    if model.status == GRB.INFEASIBLE:
        print("Model is infeasible.")
    elif model.status == GRB.UNBOUNDED:
        print("Model is unbounded.")
    else:
        print("Optimization was stopped with status", model.status)

```

    Gurobi Optimizer version 12.0.1 build v12.0.1rc0 (linux64 - "Ubuntu 24.04.2 LTS")
    
    CPU model: Intel(R) Core(TM) Ultra 7 165U, instruction set [SSE2|AVX|AVX2]
    Thread count: 14 physical cores, 14 logical processors, using up to 14 threads
    
    Optimize a model with 77 rows, 52 columns and 203 nonzeros
    Model fingerprint: 0x4506a16b
    Variable types: 0 continuous, 52 integer (52 binary)
    Coefficient statistics:
      Matrix range     [8e-02, 4e+00]
      Objective range  [1e+00, 5e+00]
      Bounds range     [1e+00, 1e+00]
      RHS range        [1e+00, 7e+00]
    
    CPU model: Intel(R) Core(TM) Ultra 7 165U, instruction set [SSE2|AVX|AVX2]
    Thread count: 14 physical cores, 14 logical processors, using up to 14 threads
    
    Optimize a model with 77 rows, 52 columns and 203 nonzeros
    Model fingerprint: 0x4506a16b
    Variable types: 0 continuous, 52 integer (52 binary)
    Coefficient statistics:
      Matrix range     [8e-02, 4e+00]
      Objective range  [1e+00, 5e+00]
      Bounds range     [1e+00, 1e+00]
      RHS range        [1e+00, 7e+00]
    Found heuristic solution: objective 26.0000000
    Presolve removed 59 rows and 28 columns
    Presolve time: 0.00s
    Presolved: 18 rows, 24 columns, 69 nonzeros
    Found heuristic solution: objective 32.0000000
    Variable types: 0 continuous, 24 integer (24 binary)
    
    Root relaxation: objective 4.514286e+01, 1 iterations, 0.00 seconds (0.00 work units)
    
        Nodes    |    Current Node    |     Objective Bounds      |     Work
     Expl Unexpl |  Obj  Depth IntInf | Incumbent    BestBd   Gap | It/Node Time
    
         0     0   45.14286    0    1   32.00000   45.14286  41.1%     -    0s
    H    0     0                      44.0000000   45.14286  2.60%     -    0s
         0     0   45.14286    0    1   44.00000   45.14286  2.60%     -    0s
    
    Explored 1 nodes (1 simplex iterations) in 0.03 seconds (0.00 work units)
    Thread count was 14 (of 14 available processors)
    
    Solution count 3: 44 32 26 
    
    Optimal solution found (tolerance 1.00e-04)
    Best objective 4.400000000000e+01, best bound 4.400000000000e+01, gap 0.0000%
    Optimal objective value: 44.0
    Enemy minions survival (z):
    z[0] = -0.0
    z[1] = -0.0
    z[2] = 1.0
    Friendly minions attacking enemy minions (x):
    x[0,0] = -0.0
    x[0,1] = -0.0
    x[0,2] = -0.0
    x[1,0] = -0.0
    x[1,1] = -0.0
    x[1,2] = -0.0
    x[2,0] = -0.0
    x[2,1] = -0.0
    x[2,2] = -0.0
    x[3,0] = -0.0
    x[3,1] = -0.0
    x[3,2] = -0.0
    x[4,0] = 0.0
    x[4,1] = 0.0
    x[4,2] = 0.0
    x[5,0] = 0.0
    x[5,1] = 0.0
    x[5,2] = 0.0
    x[6,0] = 1.0
    x[6,1] = 1.0
    x[6,2] = 1.0
    x[7,0] = 0.0
    x[7,1] = 0.0
    x[7,2] = 0.0
    Friendly minions survival (y):
    y[0] = 1.0
    y[1] = 1.0
    y[2] = 1.0
    y[3] = 1.0
    y[4] = 1.0
    y[5] = 0.0
    y[6] = 1.0
    y[7] = 0.0
    Cards played (u):
    u[0] = 1.0
    u[1] = 0.0
    u[2] = 1.0
    u[3] = 0.0
    Taunt present: -0.0
    ds_active[0] = 0.0
    ds_active[1] = 0.0
    ds_active[2] = 0.0

