"""This module helps with bookeeping for board game Alchemist."""

from functools import reduce
import itertools
from prettytable import PrettyTable
import numpy as np


INGREDIENTS = ['Bird claw', 'Scorpion', 'Toad', 'Mushroom', 'Fern',
               'Frog', 'Feather', 'Mandrage root']

INGREDIENTS_SHORTCUTS = ['b', 's', 't', 'mu', 'fer', 'fr', 'fea', 'ma']

COMBINATIONS = ['r-g+B-', 'R-G-B-', 'R+g+b-', 'r+g-B+', 'R+G+B+', 'r-G+b+', 'r+G-b-', 'R-g-b+']

POTIONS = ['R+', 'R-', 'G+', 'G-', 'B+', 'B-', 'N']

class State:
    """Game state class"""
    def __init__(self):
        self.potions_made_table = np.array(
            [['' for x in range(len(INGREDIENTS))]
             for y in range(len(INGREDIENTS))], dtype=object)
        self.illegal_combinations_table = np.array(
            [[False for x in range(len(INGREDIENTS))]
             for y in range(len(COMBINATIONS))], dtype=object)
        self.ingredients_combinations_table = np.array(
            [['' for x in range(len(INGREDIENTS))]
             for y in range(len(COMBINATIONS))], dtype=object)
        self.known_table = np.array(['' for x in range(len(INGREDIENTS))], dtype=object)

    def make_known_table(self, illegal_matrix):
        """Makes a list of known facts about ingredients based on matrix of illegal combinations."""
        result = np.array(['' for x in range(len(INGREDIENTS))], dtype=object)
        for ingredient_index, _ in enumerate(INGREDIENTS):
            legal_column = [not x for x in illegal_matrix[:, ingredient_index]]
            remaining_combinations = list(itertools.compress(COMBINATIONS, legal_column))

            known_facts = ''
            for symbol in range(0, 6):
                known_facts = known_facts + reduce(
                    (lambda sum, value: sum if sum == value else '?'),
                    [x[symbol] for x in remaining_combinations])

            result[ingredient_index] = known_facts
        return result

    def make_illegal_brew_matrix(self):
        """Makes a matrix of illegal combinations based on self.potions_made_table."""
        swap_signs_translate = ''.maketrans('+-', '-+')

        brewed_illegal = np.array(
            [[False for x in range(len(INGREDIENTS))]
             for y in range(len(COMBINATIONS))], dtype=object)

        # Find impossible combinations
        for ingredient_index, _ in enumerate(INGREDIENTS):
            potions_made_reversed = [x.lower().translate(swap_signs_translate)
                                     for x in self.potions_made_table[ingredient_index]
                                     if x != '' and x != 'N']
            for combination_index, combination in enumerate(COMBINATIONS):
                if any([potion in combination.lower() for potion in potions_made_reversed]) == True:
                    brewed_illegal[combination_index, ingredient_index] = True

        # If two things made a potion and one side is known, eliminate more choices
        known_table = self.make_known_table(brewed_illegal)
        for ingredient_index, _ in enumerate(INGREDIENTS):
            known_ingredient1 = known_table[ingredient_index]
            for ingredient2_index, _ in enumerate(INGREDIENTS):
                potion = self.potions_made_table[ingredient_index, ingredient2_index]
                known_ingredient2 = known_table[ingredient2_index]

                if potion != '' and potion in known_ingredient1:
                    illegal = [index for index, value in enumerate(COMBINATIONS)
                               if not potion.lower() in value]
                    brewed_illegal[np.array(illegal), ingredient2_index] = True
                elif potion != '' and potion.lower() in known_ingredient1:
                    illegal = [index for index, value in enumerate(COMBINATIONS)
                               if not potion in value]
                    brewed_illegal[np.array(illegal), ingredient2_index] = True
                elif potion != '' and potion in known_ingredient2:
                    illegal = [index for index, value in enumerate(COMBINATIONS)
                               if not potion.lower() in value]
                    brewed_illegal[np.array(illegal), ingredient_index] = True
                elif potion != '' and potion.lower() in known_ingredient2:
                    illegal = [index for index, value in enumerate(COMBINATIONS)
                               if not potion in value]
                    brewed_illegal[np.array(illegal), ingredient_index] = True

        return brewed_illegal

    def simplify_illegal_matrix(self, illegal_matrix):
        """Futher adjusts illegal combinations matrix based on only one legal combination rule."""
        # If something is 100% other ingredients can't be that one
        result = illegal_matrix
        for ingredient_index, _ in enumerate(INGREDIENTS):
            column = result[:, ingredient_index]
            possible = [index for index, value in enumerate(column) if value == False]
            if len(possible) == 1:
                result[possible[0], :] = True
                result[possible[0], ingredient_index] = False

        return result

    def is_legall_permutation(self, illegal_matrix, permutation):
        """Returns if a permutation of ingredients (a solution of game)
         is legal assuming illegal combinations matrix."""
        permutation_indexes = [INGREDIENTS.index(x) for x in permutation]
        return not any(illegal_matrix[combination_index, ingredient_index] for
                       combination_index, ingredient_index in enumerate(permutation_indexes))

    def recalculate(self):
        """Recalculate all of the matrices based on self.potions_made_table."""

        self.illegal_combinations_table = self.simplify_illegal_matrix(
            self.make_illegal_brew_matrix())

        self.known_table = self.make_known_table(self.illegal_combinations_table)

        self.probability_recalculate()

    def probability_recalculate(self):
        """Recalculate self.ingredients_combinations_table
        based on self.illegal_combinations_table."""
        self.ingredients_combinations_table.fill('')

        all_combinations = len([perm for perm in itertools.permutations(INGREDIENTS)
                                if self.is_legall_permutation(
                                    self.illegal_combinations_table, perm)])

        for ingredient_index, _ in enumerate(INGREDIENTS):
            column = self.illegal_combinations_table[:, ingredient_index]
            possible = [index for index, value in enumerate(column) if not value]
            for combination_index, _ in enumerate(COMBINATIONS):
                if self.illegal_combinations_table[combination_index, ingredient_index]:
                    self.ingredients_combinations_table[combination_index, ingredient_index] = '0%'
                elif len(possible) == 1:
                    self.ingredients_combinations_table[combination_index, ingredient_index] = \
                    '100%' if not\
                    self.illegal_combinations_table[combination_index, ingredient_index] \
                    else '0%'
                else:
                    costum_illegal = np.copy(self.illegal_combinations_table)
                    costum_illegal[:, ingredient_index] = True
                    costum_illegal[combination_index, ingredient_index] = False
                    costum_illegal = self.simplify_illegal_matrix(costum_illegal)
                    combinations = len([perm for perm in itertools.permutations(INGREDIENTS)
                                        if self.is_legall_permutation(costum_illegal, perm)])
                    self.ingredients_combinations_table[combination_index, ingredient_index] =\
                    '{:.0f}%'.format(100.0 * float(combinations) / all_combinations)

    def add_potion(self, ingredient1, ingredient2, potion):
        """Add potion to made table and recalculate."""
        ingredient1_index = INGREDIENTS.index(ingredient1)
        ingredient2_index = INGREDIENTS.index(ingredient2)
        self.potions_made_table[ingredient1_index, ingredient2_index] = potion
        self.potions_made_table[ingredient2_index, ingredient1_index] = potion
        self.recalculate()

    def print_combinations_table(self):
        """Pretty print probability table of combinations."""
        table = PrettyTable(['Comb/Ingr']+INGREDIENTS)

        for row in range(0, len(COMBINATIONS)):
            made_row = np.insert(self.ingredients_combinations_table[row], 0, COMBINATIONS[row])
            table.add_row(made_row)

        print(table)

    def print_made_table(self):
        """Pretty print table of made potions."""
        table = PrettyTable(['Ingredient']+INGREDIENTS)

        for row in range(0, len(INGREDIENTS)):
            made_row = np.insert(self.potions_made_table[row], 0, INGREDIENTS[row])
            made_row[row+1] = 'X'
            table.add_row(made_row)

        print(table)

    def print_known_table(self):
        """Pretty print table of known facts about  ingredients."""
        table = PrettyTable(['Ingredient']+INGREDIENTS)

        made_row = ['Known'] + self.known_table.tolist()
        table.add_row(made_row)

        print(table)

def brew_potion(state):
    """Prompt user about brewed potion and add it to the state."""
    potion = input('Which potion did you brew? ({})\n'.format(','.join(POTIONS)))
    while not potion in POTIONS:
        potion = input('Which potion did you brew? ({})\n'.format(','.join(POTIONS)))

    ingredient1 = input('What was the first ingredient? Possible ingredients are {}.\
    \n Shortcuts: {}\n'.format(','.join(INGREDIENTS), ','.join(INGREDIENTS_SHORTCUTS)))
    while not (ingredient1 in INGREDIENTS or ingredient1 in INGREDIENTS_SHORTCUTS):
        ingredient1 = input('What was the first ingredient? ({})\n'\
        .format(','.join(INGREDIENTS_SHORTCUTS)))
    if ingredient1 in INGREDIENTS_SHORTCUTS:
        index = INGREDIENTS_SHORTCUTS.index(ingredient1)
        ingredient1 = INGREDIENTS[index]
    ingredient2 = input('What was the second ingredient? Possible ingredients are {}.\n \
    Shortcuts: {}\n'.format(','.join(INGREDIENTS), ','.join(INGREDIENTS_SHORTCUTS)))
    while not (ingredient2 in INGREDIENTS or ingredient2 in INGREDIENTS_SHORTCUTS):
        ingredient2 = input('What was the second ingredient? ({})\n'\
        .format(','.join(INGREDIENTS_SHORTCUTS)))
    if ingredient2 in INGREDIENTS_SHORTCUTS:
        index = INGREDIENTS_SHORTCUTS.index(ingredient2)
        ingredient2 = INGREDIENTS[index]
    state.add_potion(ingredient1, ingredient2, potion)
    print_state(state)

def exit_game(state):
    """Do nothing."""
    return

def print_state(state):
    """Print state."""
    state.print_made_table()
    state.print_combinations_table()
    state.print_known_table()

def main():
    """Starts main loop of commands."""

    state = State()

    commands = {'exit': exit_game, 'brew': brew_potion, 'print': print_state}
    command = ''

    while command != 'exit':
        command = input('Enter a command ({}):'.format(','.join(commands.keys())))
        if command in commands:
            commands[command](state)

if __name__ == "__main__":
    main()
