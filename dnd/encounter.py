import os

from functools import cmp_to_key, partial
from random import randint
from re import compile as compile_regex

INITIATIVE_DIE_SIZE = 10

# Default colors available among Roll20 token icons
COLORS = [
    "Red",
    "Blue",
    "Green",
    "Purple",
    "Pink",
    "Yellow",
    "Brown"
]

PARTY = [
    ("Braaggi", 3),
    ("Circe", 5),
    ("Pipes", 7),
    ("Tom", 6),
    ("Vorbith", 2)
]

HP_PATTERN = compile_regex(r'(?P<hp>\d+)(\/(?P<max_hp>\d+))?')


def clear():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')


def main():
    clear()
    encounter = Encounter(PARTY)
    EncounterPlayer(encounter).play()
    return


class Encounter:

    def __init__(self, party):
        self.party = party
        self.pcs = self.roll_pcs()
        self.monsters = self.add_monsters()
        self.combatants = self.pcs + self.monsters

    def roll_pcs(self):
        return [Combatant(
            pc[0],
            self.roll_initiative(pc[1]),
            self.get_hit_points(pc[0])
        ) for pc in self.party]

    def add_monsters(self):
        monsters = []
        add_more = True
        while add_more:
            monster_name = input("Enter a monster name (leave empty to continue): ")
            if monster_name == '':
                add_more = False
            else:
                monsters = monsters + self.add_monster(monster_name)

        return monsters

    def add_monster(self, monster_name):
        names = self.get_multiple_names(monster_name)
        initiative_bonus = self.get_initiative_bonus(monster_name)
        hit_points = self.get_hit_points(monster_name)
        return [Combatant(
            n,
            self.roll_initiative(initiative_bonus),
            hit_points
        ) for n in names]

    @staticmethod
    def roll_initiative(initiative_bonus):
        return randint(1, INITIATIVE_DIE_SIZE) + initiative_bonus

    @staticmethod
    def get_hit_points(combatant_name):
        while True:
            hp = input(f"(Optional) Enter hit points for {combatant_name} (y or x/y): ")
            if hp == '':
                return 0, 0
            else:
                m = HP_PATTERN.match(hp)
                if m:
                    if m.group("max_hp"):
                        return int(m.group("hp")), int(m.group("max_hp"))
                    return int(m.group("hp")), int(m.group("hp"))
            print("Enter a number for maximum HP, or a ratio like 17/38")

    def get_multiple_names(self, monster_name):
        monster_number = self.get_number(monster_name)
        if monster_number == 1:
            return [monster_name]
        return [f"{monster_name} ({COLORS[i]})" for i in range(monster_number)]

    @staticmethod
    def get_number(monster_name):
        monster_number = 0
        while 1 > monster_number or monster_number > len(COLORS):
            try:
                monster_number = int(input(f"How many {monster_name}?: "))
                if monster_number > len(COLORS):
                    print("Come on, switch it up")
            except Exception:
                print("Try again")
        return monster_number

    @staticmethod
    def get_initiative_bonus(monster_name):
        initiative_bonus = None
        while initiative_bonus is None:
            try:
                initiative_bonus = int(input(f"Enter initiative bonus for {monster_name}: "))
            except Exception:
                print("Try again")
        return initiative_bonus


class EncounterPlayer:

    def __init__(self, encounter):
        self.encounter = encounter
        self.keep_playing = True

        # NOTE: self.sort_by_side displays PCs followed by monsters rather than initiative order.
        # To play with traditional initiative rules, replace it with self.sort_by_initiative.
        # self.sort = self.sort_by_initiative
        # or
        self.sort = self.sort_by_side

        self.active = self.encounter.combatants.copy()
        self.ordered = self.sort_by_initiative(self.active)
        self.acted = []

    def play(self):

        while self.keep_playing:
            while self.keep_playing and self.ordered != []:
                self.keep_playing = self.turn_prompt()
            self.acted = []
            self.ordered = self.sort(self.active)
            self.tick_effects()
        return

    @staticmethod
    def sort_by_side(combatants):
        return combatants.copy()

    def sort_by_initiative(self, combatants):
        return sorted(combatants, key=cmp_to_key(self.initiative_comparator))

    @staticmethod
    def initiative_comparator(combatant1, combatant2):
        if combatant1.initiative > combatant2.initiative:
            return -1
        return 1

    def turn_prompt(self):
        base_cases = {
            "q": lambda: self.false(),
            "s": lambda: self.empty_ordered(),
            "d": lambda: self.damage_prompt(),
            "h": lambda: self.heal_prompt(),
            "a": lambda: self.add_effect_prompt(),
            "r": lambda: self.remove_effect_prompt()
        }
        callback_map = CallbackMap(range(len(self.ordered)), self.take_turn, base_cases)

        clear()
        self.print_main_menu()
        callback = None
        while callback is None:
            option = input(
                "Select a number to take turn, or " +
                "apply (d)amage or (h)ealing, (a)dd or (r)emove effects, " +
                "(s)kip to next turn, or (q)uit: "
            )
            callback = callback_map.get(option)

        return callback()

    @staticmethod
    def true():
        return True

    @staticmethod
    def false():
        return False

    def empty_ordered(self):
        self.ordered = []
        return True

    def damage_prompt(self):
        base_cases = {
            "b": lambda: self.true()
        }
        callback_map = CallbackMap(self.active, self.apply_damage, base_cases)

        clear()
        self.print_damage_menu()
        callback = None
        while callback is None:
            option = input("Select a number to damage combatant, or go (b)ack: ")
            callback = callback_map.get(option)

        return callback()

    def heal_prompt(self):
        base_cases = {
            "b": lambda: self.true()
        }
        callback_map = CallbackMap(self.encounter.combatants, self.apply_healing, base_cases)

        clear()
        self.print_all_combatants_menu()
        callback = None
        while callback is None:
            option = input("Select a number to heal combatant, or go (b)ack: ")
            callback = callback_map.get(option)

        return callback()

    def add_effect_prompt(self):
        base_cases = {
            "b": lambda: self.true()
        }

        clear()
        effect_name = ''
        while effect_name == '':
            effect_name = input("Enter name for effect, or go (b)ack: ")
        if effect_name == 'b':
            return True
        effect_turns = 0
        while effect_turns == 0:
            turns_input = input(f"How many turns will {effect_name} last? (Leave blank for ongoing): ")
            if turns_input == '':
                effect_turns = None
                break
            try:
                effect_turns = int(turns_input)
            except Exception:
                print("Try again")

        callback_map = CallbackMap(self.encounter.combatants,
                                   self.add_effect,
                                   base_cases,
                                   **dict(effect_name=effect_name, effect_turns=effect_turns))

        self.print_all_combatants_menu()
        callbacks = None
        while callbacks is None:
            combatant_input = input(
                f"Select a number or comma-separated numbers for combatants to receive {effect_name}: ")
            try:
                callbacks = filter(lambda y: y is not None,
                                   [callback_map.get(x) for x in combatant_input.split(',')])
            except Exception:
                print("Try again")

        success = True
        for callback in callbacks:
            success = callback() and success
        return success

    def remove_effect_prompt(self):
        base_cases = {
            "b": lambda: self.true()
        }

        effects = []
        for combatant in self.encounter.combatants:
            effects += [(combatant, effect_name) for effect_name in combatant.effects.keys()]
        callback_map = CallbackMap(effects,
                                   self.remove_effect,
                                   base_cases)

        clear()
        self.print_current_effects_menu()
        callbacks = None
        while callbacks is None:
            effect_input = input(
                f"Select a number or comma-separated numbers to remove effects: ")
            try:
                callbacks = filter(lambda y: y is not None,
                                   [callback_map.get(x) for x in effect_input.split(',')])
            except Exception:
                print("Try again")

        success = True
        for callback in callbacks:
            success = callback() and success
        return success

    def take_turn(self, index):
        self.acted.append(self.ordered.pop(index))
        return True

    def print_main_menu(self):
        for combatant in self.acted:
            print(f"\N{CHECK MARK} {combatant}")
        print('')
        for i in range(len(self.ordered)):
            print(f"{i + 1}. {self.ordered[i]}")
        print('')
        for combatant in self.encounter.combatants:
            if combatant.hit_points[0] == 0 and combatant.hit_points[1] > 0:
                print(f"\N{CROSS MARK} {combatant}")

    def apply_damage(self, combatant):
        damage = -1
        while damage < 0:
            try:
                damage = int(input(f"How much damage to {combatant.name}?: "))
                if damage > -1:
                    break
            except Exception:
                pass
            print("Try again")
        new_hp = combatant.hit_points[0] - damage
        if combatant.hit_points[1] != 0:
            new_hp = max(0, new_hp)
        combatant.hit_points = (new_hp, combatant.hit_points[1])
        if new_hp == 0:
            self.active = [c for c in self.active if c.name != combatant.name]
            self.ordered = [c for c in self.ordered if c.name != combatant.name]
        return True

    def print_damage_menu(self):
        for i in range(len(self.active)):
            print(f"{i + 1}. {self.active[i]}")

    def apply_healing(self, combatant):
        healing = -1
        while healing < 0:
            try:
                healing = int(input(f"How many hit points to restore to {combatant.name}?: "))
                if healing > -1:
                    break
            except Exception:
                pass
            print("Try again")
        new_hp = min(combatant.hit_points[0] + healing, combatant.hit_points[1])
        combatant.hit_points = (new_hp, combatant.hit_points[1])
        self.active = [c for c in self.encounter.combatants if c.hit_points[0] > 0 or c.hit_points[1] == 0]
        return True

    def print_all_combatants_menu(self):
        for i in range(len(self.encounter.combatants)):
            print(f"{i + 1}. {self.encounter.combatants[i]}")

    @staticmethod
    def add_effect(combatant, effect_name, effect_turns):
        combatant.add_effect(Effect(effect_name, effect_turns))
        return True

    def print_current_effects_menu(self):
        i = 1
        for combatant in self.encounter.combatants:
            if len(combatant.effects) > 0:
                print(combatant.name)
                for effect in combatant.effects:
                    print(f"{i}. {effect}")
                    i += 1

    @staticmethod
    def remove_effect(combatant_and_effect_name):
        combatant, effect_name = combatant_and_effect_name
        combatant.remove_effect(effect_name)
        return True

    def tick_effects(self):
        for combatant in self.encounter.combatants:
            combatant.effects = {name: effect for (name, effect) in combatant.effects.items() if effect.tick()}


class Combatant:

    def __init__(self, name, initiative, hit_points):
        self.name = name
        self.initiative = initiative
        self.hit_points = hit_points
        self.effects = dict()

    def add_effect(self, effect):
        self.effects[effect.name] = effect

    def remove_effect(self, effect_name):
        self.effects = {name: effect for (name, effect) in self.effects.items() if name != effect_name}

    def __str__(self):
        s = f"{self.name} ({self.hit_points[0]}/{self.hit_points[1]})"
        effects = self.effects.values()
        if len(effects) > 0:
            s += f"[{', '.join([str(e) for e in effects])}]"
        return s


class Effect:

    def __init__(self, name, turns):
        self.name = name
        self.turns = turns

    def tick(self):
        if self.turns is None:
            return True
        self.turns -= 1
        if self.turns > 0:
            return True
        return False

    def __str__(self):
        if self.turns is not None:
            return f"{self.name} ({self.turns})"
        return self.name


class CallbackMap:
    def __init__(self, options, action, base_cases=None, **kwargs):
        if base_cases is None:
            base_cases = dict()
        if kwargs is None:
            kwargs = dict()
        cases = {}
        for i in range(len(options)):
            cases[str(i + 1)] = partial(action, options[i], **kwargs)
        self.cases = {**cases, **base_cases}

    def get(self, case):
        return self.cases.get(case, None)


main()
