from functools import cmp_to_key, partial
from os import name, system
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

party = [
  ("Braaggi", 3),
  ("Circe", 5),
  ("Pipes", 7),
  ("Tom", 6),
  ("Vorbith", 2)
]

HP_PATTERN = compile_regex(r'(?P<hp>\d+)(\/(?P<max_hp>\d+))?')

def clear():
  # for windows
  if name == 'nt':
    _ = system('cls')

  # for mac and linux(here, os.name is 'posix')
  else:
    _ = system('clear')

def main():
  encounter = Encounter(party)
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

  def roll_initiative(self, initiative_bonus):
    return randint(1, INITIATIVE_DIE_SIZE) + initiative_bonus

  def get_hit_points(self, combatant_name):
    while True:
      hp = input("(Optional) Enter hit points for %s (y or x/y): " % combatant_name)
      if hp == '':
        return (0, 0)
      else:
        m = HP_PATTERN.match(hp)
        if m:
          if m.group("max_hp"):
            return (int(m.group("hp")), int(m.group("max_hp")))
          return (int(m.group("hp")), int(m.group("hp")))
      print("Enter a number for maximum HP, or a ratio like 17/38")

  def get_multiple_names(self, monster_name):
    monster_number = self.get_number(monster_name)
    if monster_number == 1:
      return [monster_name]
    return ["%s (%s)" % (monster_name, COLORS[i]) for i in range(monster_number)]

  def get_number(self, monster_name):
    monster_number = 0
    while 1 > monster_number or monster_number > len(COLORS):
      try:
        monster_number = int(input("How many %s?: " % monster_name))
        if monster_number > len(COLORS):
          print("Come on, switch it up")
      except:
        print("Try again")
    return monster_number

  def get_initiative_bonus(self, monster_name):
    initiative_bonus = None
    while initiative_bonus == None:
      try:
        initiative_bonus = int(input("Enter initiative bonus for %s: " % monster_name))
      except:
        print("Try again")
    return initiative_bonus


class EncounterPlayer:

  def __init__(self, encounter):
    self.encounter = encounter
    self.keep_playing = True
    # self.sort = self.sort_by_initiative
    # or
    self.sort = self.sort_by_side

  def play(self):
    # NOTE: self.sort_by_side displays PCs followed by monsters rather than initiative order.
    # To play with traditional initiative rules, replace it with self.sort_by_initiative.
    self.active = self.encounter.combatants.copy()
    self.ordered = self.sort_by_initiative(self.active)
    self.acted = []
    while self.keep_playing:
      while self.keep_playing and self.ordered != []:
        self.keep_playing = self.turn_prompt()
      self.acted = []
      self.ordered = self.sort(self.active)
    return

  def sort_by_side(self, combatants):
    return combatants.copy()

  def sort_by_initiative(self, combatants):
    return sorted(combatants, key=cmp_to_key(self.initiative_comparator))

  def initiative_comparator(self, combatant1, combatant2):
    if combatant1.initiative > combatant2.initiative:
      return -1
    return 1

  def turn_prompt(self):
    base_cases = {
      "q": lambda: self.false(),
      "s": lambda: self.empty_ordered(),
      "d": lambda: self.damage_prompt()
    }
    switcher = OptionSwitcher(len(self.ordered), self.take_turn, base_cases)

    clear()
    self.print_main_menu()
    callback = None
    while callback == None:
      option = input(
         "Select a number to take turn, or " +
         "apply (d)amage or (h)ealing, (s)kip to next turn, or (q)uit: "
      )
      callback = switcher.get(option)

    return callback()

  def true(self):
    return True

  def false(self):
    return False

  def empty_ordered(self):
    self.ordered = []
    return True

  def damage_prompt(self):
    base_cases = {
      "b": lambda: self.true()
    }
    switcher = OptionSwitcher(len(self.active), self.apply_damage, base_cases)

    clear()
    self.print_damage_menu()
    callback = None
    while callback == None:
      option = input("Select a number to damage combatant, or go (b)ack: ")
      callback = switcher.get(option)

    return callback()

  def take_turn(self, index):
    self.acted.append(self.ordered.pop(index))
    return True

  def print_main_menu(self):
    for combatant in self.acted:
      print("\N{CHECK MARK} %s" % combatant.name)
    print('')
    for i in range(len(self.ordered)):
      print("%d. %s (%d/%d)" % (
        i + 1,
        self.ordered[i].name,
        self.ordered[i].hit_points[0],
        self.ordered[i].hit_points[1]
      ))
    print('')
    for combatant in self.encounter.combatants:
      if combatant.hit_points[0] == 0 and combatant.hit_points[1] > 0:
        print("\N{CROSS MARK} %s" % combatant.name)

  def apply_damage(self, index):
    combatant = self.active[index]
    damage = -1
    while damage < 0:
      try:
        damage = int(input("How much damage to %s?: " % combatant.name))
        if damage > -1:
          break
      except:
        pass
      print("Try again")
    new_hp = combatant.hit_points[0] - damage
    if combatant.hit_points[1] != 0:
      new_hp = max(0, new_hp)
    combatant.hit_points = (new_hp, combatant.hit_points[1])
    if new_hp == 0:
      self.active.pop(index)
      self.ordered = [c for c in self.ordered if c.name != combatant.name]
    return True

  def print_damage_menu(self):
    for i in range(len(self.active)):
      print("%d. %s (%d/%d)" % (
        i + 1,
        self.active[i].name,
        self.active[i].hit_points[0],
        self.active[i].hit_points[1]
      ))

class Combatant:

  def __init__(self, name, initiative, hit_points):
      self.name = name
      self.initiative = initiative
      self.hit_points = hit_points


class OptionSwitcher:

  def __init__(self, num_options, action, base_cases={}):
    self.action = action
    self.cases = self.create_cases(num_options)
    self.cases = {**self.cases, **base_cases}

  def create_cases(self, num_options):
    cases = {}
    for i in range(num_options):
      cases[str(i+1)] = partial(self.action, i)
    return cases

  def get(self, case):
    return self.cases.get(case, None)


main()
