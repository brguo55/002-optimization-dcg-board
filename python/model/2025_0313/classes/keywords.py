# classes/keywords.py

from typing import List

class Keywords:
    """
    Manages Hearthstone keywords, focusing on Paladin, Warrior, Demon Hunter, and Hunter.
    """

    GENERAL_KEYWORDS = {
        "Taunt", "Charge", "Rush",
        "Battlecry", "Deathrattle",
        "Windfury", "Lifesteal", "Poisonous", "Stealth",
        "Divine Shield"
    }

    CLASS_KEYWORDS = {
        "Paladin": {"Divine Shield", "Taunt"},
        "Warrior": {"Taunt", "Rush"},
        "Demon Hunter": {"Rush", "Lifesteal"},
        "Hunter": {"Deathrattle", "Stealth"}
    }

    def __init__(self, keywords: List[str] = None, minion_class: str = "Neutral"):
        """
        :param keywords: List of possible keywords (e.g., ["Taunt", "Charge"]).
        :param minion_class: The class for the minion ("Paladin", "Warrior", etc.).
        """
        allowed = self.GENERAL_KEYWORDS.union(
            self.CLASS_KEYWORDS.get(minion_class, set())
        )
        # Only keep the keywords that are allowed for the given class
        self.keywords = {kw for kw in (keywords or []) if kw in allowed}

    def add_keyword(self, keyword: str, minion_class: str = "Neutral"):
        """
        Adds a keyword if it's valid for the given minion_class.
        """
        allowed = self.GENERAL_KEYWORDS.union(
            self.CLASS_KEYWORDS.get(minion_class, set())
        )
        if keyword in allowed:
            self.keywords.add(keyword)
        else:
            print(f"{keyword} is not allowed for {minion_class} minions.")

    def remove_keyword(self, keyword: str):
        """
        Removes the specified keyword if it exists; if not, does nothing.
        """
        self.keywords.discard(keyword)

    def has_keyword(self, keyword: str) -> bool:
        """
        Returns True if this object contains the specified keyword, False otherwise.
        """
        return keyword in self.keywords

    def __str__(self):
        """
        Returns a comma-separated string of this object's keywords, sorted alphabetically.
        """
        return ", ".join(sorted(self.keywords))