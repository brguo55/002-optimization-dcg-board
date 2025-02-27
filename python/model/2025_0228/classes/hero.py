# hero.py

class Hero:
    """
    Represents a Hearthstone hero with certain properties and a simplified hero power.
    """

    def __init__(self, hero_class: str, health: int = 30, armor: int = 0):
        """
        :param hero_class: e.g. "Demon Hunter", "Druid", "Hunter", "Mage", "Paladin",
                           "Priest", "Rogue", "Shaman", "Warlock", or "Warrior"
        :param health: Hero's starting health (default 30).
        :param armor: Hero's starting armor (default 0).
        """
        self.hero_class = hero_class
        self.health = health
        self.armor = armor

    def use_hero_power(self):
        """
        Apply the effect of the hero power for one turn.
        Subclass or expand each hero's logic as you see fit.

        This function returns a tuple describing the effect, or None if not implemented.
        (Damage, Summon, Heal, Armor, etc.)
        """
        # Each hero's unique effect
        if self.hero_class == "Demon Hunter":
            # Gains +1 Attack this turn (in real Hearthstone).
            # We'll just say "attack +1" as a placeholder.
            return ("Attack", 1)

        elif self.hero_class == "Druid":
            # Gains +1 Attack this turn AND +1 Armor (Shapeshift).
            return ("Attack_and_Armor", 1)

        elif self.hero_class == "Hunter":
            # Deals 2 damage to the enemy hero (Steady Shot).
            return ("Damage_EnemyHero", 2)

        elif self.hero_class == "Mage":
            # Deals 1 damage to any target (Fireblast).
            return ("Damage_AnyTarget", 1)

        elif self.hero_class == "Paladin":
            # Summons a 1/1 Silver Hand Recruit (Reinforce).
            # You could return a minion object, but we'll do a placeholder:
            return ("Summon", "Silver Hand Recruit")

        elif self.hero_class == "Priest":
            # Heals any character for 2 (Lesser Heal).
            return ("Heal_AnyTarget", 2)

        elif self.hero_class == "Rogue":
            # Equips a 1/2 dagger weapon (Dagger Mastery).
            # We'll represent a "Weapon" by returning some placeholder:
            return ("Weapon", {"attack": 1, "durability": 2})

        elif self.hero_class == "Shaman":
            # Summons a random basic Totem (Totemic Call).
            # We'll do a placeholder "Random Totem".
            return ("Summon", "Random Totem")

        elif self.hero_class == "Warlock":
            # Draw a card and take 2 damage (Life Tap).
            # We'll represent that as:
            return ("Draw_Card_and_SelfDamage", 2)

        elif self.hero_class == "Warrior":
            # Gain 2 Armor (Armor Up!).
            self.armor += 2
            return ("Armor", 2)

        else:
            # Unrecognized hero class
            print(f"[Hero Power] {self.hero_class} is not recognized.")
            return None

    def __str__(self):
        return f"Hero({self.hero_class}, Health={self.health}, Armor={self.armor})"

