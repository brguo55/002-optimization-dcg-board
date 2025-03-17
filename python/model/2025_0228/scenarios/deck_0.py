# scenarios/deck_example.py

import random
from classes.minion import Minion

deck_15 = [
    Minion("Goldshire Footman", "Neutral", ["Taunt"], attack=1, health=2, strat_value=1, mana_cost=1),
    Minion("Murloc Raider", "Neutral", [], attack=2, health=1, strat_value=1, mana_cost=1),
    Minion("Bloodfen Raptor", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    Minion("River Crocolisk", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    Minion("Frostwolf Grunt", "Neutral", ["Taunt"], attack=2, health=2, strat_value=1, mana_cost=2),
    Minion("Amani Berserker", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    Minion("Bluegill Warrior", "Neutral", ["Charge"], attack=2, health=1, strat_value=1, mana_cost=2),
    Minion("Faerie Dragon", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    Minion("Wolfrider", "Neutral", ["Charge"], attack=3, health=1, strat_value=1, mana_cost=3),
    Minion("Silverback Patriarch", "Neutral", ["Taunt"], attack=1, health=4, strat_value=1, mana_cost=3),
    Minion("Ironfur Grizzly", "Neutral", ["Taunt"], attack=3, health=3, strat_value=1, mana_cost=3),
    Minion("Chillwind Yeti", "Neutral", [], attack=4, health=5, strat_value=1, mana_cost=4),
    Minion("Sen'jin Shieldmasta", "Neutral", ["Taunt"], attack=3, health=5, strat_value=1, mana_cost=4),
    Minion("Stormwind Knight", "Neutral", ["Charge"], attack=2, health=5, strat_value=1, mana_cost=4),
    Minion("Gnomish Inventor", "Neutral", [], attack=2, health=4, strat_value=1, mana_cost=4),
]

def draw_random_card(deck_list):
    """
    Draws one random card from deck_list and returns it.
    If deck is empty, returns None.
    """
    if not deck_list:
        return None
    card = random.choice(deck_list)
    deck_list.remove(card)
    return card

def add_card_to_hand(deck_list, hand_list):
    """
    Draws one random card from 'deck_list' and appends it to 'hand_list'.
    Returns the card drawn, or None if deck is empty.
    """
    card = draw_random_card(deck_list)
    if card is not None:
        hand_list.append(card)
    return card

