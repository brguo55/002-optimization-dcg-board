from classes.minion import Minion
import random

# A simpler deck with just 5 neutral minions
deck = [
    Minion("Murloc Raider", "Neutral", [], attack=2, health=1, strat_value=1, mana_cost=1),
    Minion("Bloodfen Raptor", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    Minion("River Crocolisk", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    Minion("Wolfrider", "Neutral", ["Charge"], attack=3, health=1, strat_value=1, mana_cost=3),
    Minion("Chillwind Yeti", "Neutral", [], attack=4, health=5, strat_value=1, mana_cost=4),
]

def draw_random_card(deck_list):
    if not deck_list:
        return None
    card = random.choice(deck_list)
    deck_list.remove(card)
    return card

def add_card_to_hand(deck_list, hand_list):
    card = draw_random_card(deck_list)
    if card is not None:
        hand_list.append(card)
    return card

