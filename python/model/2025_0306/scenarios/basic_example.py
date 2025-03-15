# scenarios/basic_example.py

from classes.minion import Minion

friendly_minions = [
    Minion(name="River Crocolisk", minion_class="Neutral", keywords=[], attack=2, health=3, strat_value=1, mana_cost=2),
    Minion(name="Silverback Patriarch", minion_class="Neutral", keywords=["Taunt"], attack=1, health=4, strat_value=1, mana_cost=3),
    Minion(name="Chillwind Yeti", minion_class="Neutral", keywords=[], attack=4, health=5, strat_value=1, mana_cost=4),
    Minion(name="Kor'kron Elite", minion_class="Warrior", keywords=["Charge"], attack=4, health=3, strat_value=1, mana_cost=4),
]

enemy_minions = [
    Minion(name="Silver Hand Recruit", minion_class="Paladin", keywords=[], attack=1, health=1, strat_value=1, mana_cost=1),
    Minion(name="Righteous Protector", minion_class="Paladin", keywords=["Taunt", "Divine Shield"], attack=1, health=1, strat_value=1, mana_cost=1),
    Minion(name="Oasis Snapjaw", minion_class="Neutral", keywords=[], attack=2, health=7, strat_value=1, mana_cost=4),
]

# Paladin hand example
paladin_hand = [
    Minion(
        name="Murloc Raider",
        minion_class="Neutral",
        keywords=[],
        attack=2,
        health=1,
        strat_value=1,
        mana_cost=1
    ),
    Minion(
        name="Bloodfen Raptor",
        minion_class="Neutral",
        keywords=[],
        attack=3,
        health=2,
        strat_value=1,
        mana_cost=2
    ),
    Minion(
        name="Kor'kron Elite",
        minion_class="Warrior",
        keywords=[],
        attack=4,
        health=3,
        strat_value=2,
        mana_cost=4
    )
]

# Warrior hand example (2 cards, as requested)
warrior_hand = [
    Minion(
        name="Amani Berserker",
        minion_class="Neutral",
        keywords=[],
        attack=2,
        health=3,
        strat_value=1,
        mana_cost=2
    ),
    Minion(
        name="Wolfrider",
        minion_class="Neutral",
        keywords=["Charge"],
        attack=3,
        health=1,
        strat_value=1,
        mana_cost=3
    )
]