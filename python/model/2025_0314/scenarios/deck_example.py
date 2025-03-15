import random
from classes.minion import Minion

# ---------------------------
# Define Paladin deck of 18 cards
# ---------------------------
paladin_deck = [
    # 1
    Minion("Goldshire Footman", "Neutral", ["Taunt"], attack=1, health=2, strat_value=1, mana_cost=1),
    # 2
    Minion("Righteous Protector", "Paladin", ["Taunt", "Divine Shield"], attack=1, health=1, strat_value=1, mana_cost=1),
    # 3
    Minion("Murloc Raider", "Neutral", [], attack=2, health=1, strat_value=1, mana_cost=1),
    # 4
    Minion("Bloodfen Raptor", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    # 5
    Minion("River Crocolisk", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    # 6
    Minion("Frostwolf Grunt", "Neutral", ["Taunt"], attack=2, health=2, strat_value=1, mana_cost=2),
    # 7
    Minion("Amani Berserker", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    # 8
    Minion("Bluegill Warrior", "Neutral", ["Charge"], attack=2, health=1, strat_value=1, mana_cost=2),
    # 9
    Minion("Faerie Dragon", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    # 10
    Minion("Wolfrider", "Neutral", ["Charge"], attack=3, health=1, strat_value=1, mana_cost=3),
    # 11
    Minion("Silverback Patriarch", "Neutral", ["Taunt"], attack=1, health=4, strat_value=1, mana_cost=3),
    # 12
    Minion("Ironfur Grizzly", "Neutral", ["Taunt"], attack=3, health=3, strat_value=1, mana_cost=3),
    # 13
    Minion("Chillwind Yeti", "Neutral", [], attack=4, health=5, strat_value=1, mana_cost=4),
    # 14
    Minion("Sen'jin Shieldmasta", "Neutral", ["Taunt"], attack=3, health=5, strat_value=1, mana_cost=4),
    # 15
    Minion("Stormwind Knight", "Neutral", ["Charge"], attack=2, health=5, strat_value=1, mana_cost=4),
    # 16
    Minion("Gnomish Inventor", "Neutral", [], attack=2, health=4, strat_value=1, mana_cost=4),
    # 17
    Minion("Scarlet Crusader", "Neutral", ["Divine Shield"], attack=3, health=1, strat_value=1, mana_cost=3),
    # 18
    Minion("Guardian of Kings", "Paladin", [], attack=5, health=6, strat_value=1, mana_cost=7),
]

# ---------------------------
# Define Warrior deck of 18 cards
# ---------------------------
warrior_deck = [
    # 1
    Minion("Goldshire Footman", "Neutral", ["Taunt"], attack=1, health=2, strat_value=1, mana_cost=1),
    # 2
    Minion("Murloc Raider", "Neutral", [], attack=2, health=1, strat_value=1, mana_cost=1),
    # 3
    Minion("Bloodfen Raptor", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    # 4
    Minion("River Crocolisk", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    # 5
    Minion("Bluegill Warrior", "Neutral", ["Charge"], attack=2, health=1, strat_value=1, mana_cost=2),
    # 6
    Minion("Wolfrider", "Neutral", ["Charge"], attack=3, health=1, strat_value=1, mana_cost=3),
    # 7
    Minion("Ironfur Grizzly", "Neutral", ["Taunt"], attack=3, health=3, strat_value=1, mana_cost=3),
    # 8
    Minion("Amani Berserker", "Neutral", [], attack=2, health=3, strat_value=1, mana_cost=2),
    # 9
    Minion("Faerie Dragon", "Neutral", [], attack=3, health=2, strat_value=1, mana_cost=2),
    # 10
    Minion("Frostwolf Grunt", "Neutral", ["Taunt"], attack=2, health=2, strat_value=1, mana_cost=2),
    # 11
    Minion("Silverback Patriarch", "Neutral", ["Taunt"], attack=1, health=4, strat_value=1, mana_cost=3),
    # 12
    Minion("Sen'jin Shieldmasta", "Neutral", ["Taunt"], attack=3, health=5, strat_value=1, mana_cost=4),
    # 13
    Minion("Stormwind Knight", "Neutral", ["Charge"], attack=2, health=5, strat_value=1, mana_cost=4),
    # 14
    Minion("Chillwind Yeti", "Neutral", [], attack=4, health=5, strat_value=1, mana_cost=4),
    # 15
    Minion("Kor'kron Elite", "Warrior", ["Charge"], attack=4, health=3, strat_value=1, mana_cost=4),
    # 16
    Minion("Redband Wasp", "Warrior", ["Rush"], attack=1, health=3, strat_value=1, mana_cost=2),
    # 17
    Minion("Stonehill Defender", "Neutral", ["Taunt"], attack=1, health=4, strat_value=1, mana_cost=3),
    # 18
    Minion("Arathi Weaponsmith", "Warrior", [], attack=3, health=3, strat_value=1, mana_cost=4),
]

def draw_random_card(deck):
    """
    Draws one random card from 'deck' and returns it.
    If deck is empty, returns None.
    """
    if not deck:
        return None
    card = random.choice(deck)
    deck.remove(card)
    return card

def add_card_to_hand(deck, hand_list):
    """
    Draws one random card from 'deck' and appends it to 'hand_list'.
    Returns the card drawn, or None if deck is empty.
    """
    card = draw_random_card(deck)
    if card is not None:
        hand_list.append(card)
    return card


