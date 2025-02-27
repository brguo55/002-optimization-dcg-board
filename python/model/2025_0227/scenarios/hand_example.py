# scenarios/hand_example.py

from classes.minion import Minion

# A simple example hand list:
hand_list = [
    Minion(name="Murloc Raider", minion_class="Neutral", keywords=[], attack=2, health=1, strat_value=1, mana_cost=1),
    Minion(name="Bloodfen Raptor", minion_class="Neutral", keywords=[], attack=3, health=2, strat_value=1, mana_cost=2),
    Minion(name="Kor'kron Elite", minion_class="Warrior", keywords=["Charge"], attack=4, health=3, strat_value=2, mana_cost=4),
]
