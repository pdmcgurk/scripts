from functools import cmp_to_key, partial
from os import name, system
from random import randint

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
    self.monsters = self.add_monsters()
    self.pcs = self.roll_pcs()
    self.combatants = self.pcs + self.monsters

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
    monsters = []

    monster_number = 0
    while 1 > monster_number or monster_number > len(COLORS):
      try:
        monster_number = int(input("How many %s?: " % monster_name))
        if monster_number > len(COLORS):
          print("Come on, switch it up")
      except:
        print("Try again")

    monster_initiative = None
    while monster_initiative == None:
      try:
        monster_initiative = int(input("Enter initiative bonus for %s: " % monster_name))
      except:
        print("Try again")

    if monster_number > 1:
      for i in range(monster_number):
        name_with_color = "%s (%s)" % (monster_name, COLORS[i])
        monsters.append(Combatant(name_with_color, self.roll_initiative(monster_initiative)))
    else:
      monsters.append(Combatant(monster_name, self.roll_initiative(monster_initiative)))

    return monsters

  def roll_initiative(self, initiative_bonus):
    return randint(1, INITIATIVE_DIE_SIZE) + initiative_bonus

  def roll_pcs(self):
    pcs = []
    for pc in self.party:
      pcs.append(Combatant(pc[0], self.roll_initiative(pc[1])))
    return pcs

class EncounterPlayer:

  def __init__(self, encounter):
    self.encounter = encounter
    self.keep_playing = True
    self.acted = []
    self.ordered = []

  def play(self):
    # NOTE: self.sort_by_side displays PCs followed by monsters rather than inititive order.
    # To play with traditional initiative rules, replace it with self.sort_by_initiative.
    self.ordered = self.sort_by_initiative()
    while self.keep_playing:
      while self.keep_playing and self.ordered != []:
        self.keep_playing = self.turn_prompt()
      self.acted = []
      self.ordered = self.sort_by_side()
    return

  def sort_by_initiative(self):
    return sorted(self.encounter.combatants, key=cmp_to_key(self.initiative_comparator))

  def initiative_comparator(self, combatant1, combatant2):
    if combatant1.initiative > combatant2.initiative:
      return -1
    return 1

  def sort_by_side(self):
    return self.encounter.combatants.copy()

  def turn_prompt(self):
    base_cases = {
      "q": lambda: self.false(),
      "s": lambda: self.empty_ordered()
    }
    switcher = OptionSwitcher(len(self.ordered), self.take_turn, base_cases)

    clear()
    self.print_options()
    callback = None
    while callback == None:
      option = input("Select number to take turn, (s)kip to next turn, or (q)uit: ")
      callback = switcher.get(option)
      
    return callback()

  def false(self):
    return False

  def empty_ordered(self):
    self.ordered = []
    return True

  def take_turn(self, index):
    self.acted.append(self.ordered.pop(index))
    return True

  def print_options(self):
    for combatant in self.acted:
      print("\N{CHECK MARK} %s" % combatant.name)
    print('')
    for i in range(len(self.ordered)):
      print("%d. %s" % (i + 1, self.ordered[i].name))


class Combatant:

  def __init__(self, name, initiative):
      self.name = name
      self.initiative = initiative


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
