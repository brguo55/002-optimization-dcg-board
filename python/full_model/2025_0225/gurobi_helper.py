from gurobipy import Model, GRB

class GurobiSolver:
    def __init__(self, game_state):
        self.game_state = game_state
        self.model = Model("Hearthstone_AI")

    def optimize_turn(self):
        """Uses integer programming to optimize AI actions."""
        self.model.setParam('OutputFlag', 0)  # Disable Gurobi console output
        
        # Decision variables
        attack = self.model.addVar(vtype=GRB.BINARY, name="attack")
        defend = self.model.addVar(vtype=GRB.BINARY, name="defend")

        # Objective: Maximize damage while keeping hero alive
        self.model.setObjective(5 * attack - 2 * defend, GRB.MAXIMIZE)

        # Constraints
        self.model.addConstr(attack + defend <= 1, "SingleAction")
        self.model.optimize()

        return "Attack" if attack.x > defend.x else "Defend"
