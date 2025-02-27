# classes/minion.py

from typing import List
from classes.keywords import Keywords

class Minion:
    """Minion class, used to hold the keywords and properties of a minion."""

    def __init__(
        self,
        name: str,
        minion_class: str = "Neutral",
        keywords: List[str] = None,
        attack: int = 0,
        health: int = 0,
        strat_value: int = 0,
        mana_cost: int = 0
    ):
        """
        :param name: Name of the minion (e.g., "Chillwind Yeti").
        :param minion_class: Class affiliation (e.g., "Paladin", "Warrior", or "Neutral").
        :param keywords: A list of strings like ["Taunt", "Divine Shield"].
        :param attack: Attack value of the minion.
        :param health: Health value of the minion.
        :param strat_value: A custom 'strategic value' integer.
        :param mana_cost: How much mana it costs to play/summon this minion.
        """
        self.name = name
        self.minion_class = minion_class
        self.attack = attack
        self.health = health
        self.strat_value = strat_value
        self.mana_cost = mana_cost

        # Initialize keywords based on the minion's class
        self.keywords = Keywords(keywords, minion_class)

    def __str__(self):
        """Returns a simple description of the minion."""
        kw_str = str(self.keywords) if self.keywords else "No Keywords"
        return (
            f"Minion: {self.name} | "
            f"Class: {self.minion_class} | "
            f"Attack: {self.attack} | "
            f"Health: {self.health} | "
            f"Keywords: {kw_str}"
        )
