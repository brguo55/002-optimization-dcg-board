# test_one_minion.py
# A minimal scenario with exactly one 4/3 friendly minion,
# one 1/4 enemy minion, an empty hand, enemy hero at 4 HP,
# and current mana = 5 (usually set in your main code).

from classes.minion import Minion

# Friendly Board: one minion with Attack=4, Health=3
friendly_minions = [
    Minion(
        name="Test Friendly Minion",
        minion_class="Neutral",
        keywords=[],
        attack=4,
        health=3,
        strat_value=1,
        mana_cost=4
    )
]

# Enemy Board: one minion with Attack=1, Health=4
enemy_minions = [
    Minion(
        name="Test Enemy Minion",
        minion_class="Neutral",
        keywords=[],
        attack=1,
        health=4,
        strat_value=1,
        mana_cost=2
    )
]

# Hand is empty
hand_list = []

