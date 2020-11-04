import math
import sys
from collections import defaultdict
import itertools
from grammar import Pcfg

def check_table_format(table):
    """
    Return true if the backpointer table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Backpointer table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and \
          isinstance(split[0], int)  and isinstance(split[1], int):
            sys.stderr.write("Keys of the backpointer table must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of backpointer table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            bps = table[split][nt]
            if isinstance(bps, str): # Leaf nodes may be strings
                continue 
            if not isinstance(bps, tuple):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Incorrect type: {}\n".format(bps))
                return False
            if len(bps) != 2:
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Found more than two backpointers: {}\n".format(bps))
                return False
            for bp in bps: 
                if not isinstance(bp, tuple) or len(bp)!=3:
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has length != 3.\n".format(bp))
                    return False
                if not (isinstance(bp[0], str) and isinstance(bp[1], int) and isinstance(bp[2], int)):
                    print(bp)
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has incorrect type.\n".format(bp))
                    return False
    return True

def check_probs_format(table):
    """
    Return true if the probability table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Probability table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and isinstance(split[0], int) and isinstance(split[1], int):
            sys.stderr.write("Keys of the probability must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of probability table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            prob = table[split][nt]
            if not isinstance(prob, float):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a float.{}\n".format(prob))
                return False
            if prob > 0:
                sys.stderr.write("Log probability may not be > 0.  {}\n".format(prob))
                return False
    return True



class CkyParser(object):
    """
    A CKY parser.
    """

    def __init__(self, grammar): 
        """
        Initialize a new parser instance from a grammar. 
        """
        self.grammar = grammar

    def is_in_language(self,tokens):
        """
        Membership checking. Parse the input tokens and return True if 
        the sentence is in the language described by the grammar. Otherwise
        return False
        """
        table = dict()

        # Initialize tables
        n = len(tokens)
        for i in range(n) :
            table[(i, i+1)] = {}

        # Initialization
        # for i in 0 ... n-1 
        for i in range(n) :
            rhs_rules = self.grammar.rhs_to_rules[(tokens[i], )]
            for rule in rhs_rules :
                table[(i, i+1)][rule[0]] = tokens[i]

        # Main Loop
        for length in range(2, n + 1) :
            for i in range(n - length + 1) :
                j = i + length
                # Dummy values for comparison
                table[(i, j)] = { "" : "" }
                for k in range(i + 1, j) :
                    l_keys = [key for (key, val) in table[(i, k)].items()]
                    if l_keys == [] :
                        # print("No LHS found")
                        continue

                    r_keys = [key for (key, val) in table[(k, j)].items()]
                    if r_keys == [] :
                        # print("No RHS found")
                        continue

                    for l_key in l_keys :
                        for r_key in r_keys :
                            rules = self.grammar.rhs_to_rules[(l_key, r_key)]
                            if rules == [] :
                                # print("No rules for :", l_key, ", ", r_key)
                                continue
                            for rule in rules :
                                table[(i, j)][rule[0]] = ((rule[1][0], i, k), (rule[1][1], k, j))

                # Dummy values removed
                table[(i, j)].pop("")

        return len(table[(0, n)]) > 0

    def parse_with_backpointers(self, tokens):
        """
        Parse the input tokens and return a parse table and a probability table.
        """
        # Keys are spans
        # Split recorded is the one that results in the most probable parse for the span
        # e.g. table[(0,3)]['NP'] = (("NP",0,2),("FLIGHTS",2,3))
        # Terminal symbols could just be represented as strings
        # e.g. table[(2,3)]["FLIGHTS"] = "flights"
        table = dict()

        # Similar to table above, but records log probabilities instead of backpointers
        # e.g. probs[(0,3)]['NP'] = -12.1324
        probs = dict()

        # Initialize tables
        n = len(tokens)
        for i in range(n) :
            table[(i, i+1)] = {}
            probs[(i, i+1)] = {}

        # Initialization
        # for i in 0 ... n-1 
        for i in range(n) :
            rhs_rules = self.grammar.rhs_to_rules[(tokens[i], )]
            for rule in rhs_rules :
                table[(i, i+1)][rule[0]] = tokens[i]
                # Store log probabilities
                probs[(i, i+1)][rule[0]] = math.log(rule[2], 2)

        # Main Loop
        for length in range(2, n + 1) :
            for i in range(n - length + 1) :
                j = i + length
                # Dummy values for comparison
                table[(i, j)] = { "" : "" }
                probs[(i, j)] = { "" : -math.inf }
                for k in range(i + 1, j) :
                    l_keys = [key for (key, val) in table[(i, k)].items()]
                    if l_keys == [] :
                        # print("No LHS found")
                        continue

                    r_keys = [key for (key, val) in table[(k, j)].items()]
                    if r_keys == [] :
                        # print("No RHS found")
                        continue

                    # print("Left keys :", l_keys)
                    # print("Right keys :", r_keys)
                    for l_key in l_keys :
                        for r_key in r_keys :
                            rules = self.grammar.rhs_to_rules[(l_key, r_key)]
                            if rules == [] :
                                # print("No rules for :", l_key, ", ", r_key)
                                continue
                            for rule in rules :
                                # Possible change here
                                # First encounter
                                if rule[0] not in probs[(i, j)] :
                                    probs[(i, j)][rule[0]] = -math.inf
                                # Update only for greater values
                                new_key = ((rule[1][0], i, k), (rule[1][1], k, j))
                                new_value = probs[(i, k)][l_key] + probs[(k, j)][r_key] + math.log(rule[2], 2)
                                if probs[(i, j)][rule[0]] < new_value :
                                    table[(i, j)][rule[0]] = new_key
                                    probs[(i, j)][rule[0]] = new_value

                # Dummy values removed
                table[(i, j)].pop("")
                probs[(i, j)].pop("")
        return table, probs


def get_tree(chart, i, j, nt): 
    """
    Return the parse-tree rooted in non-terminal nt and covering span i,j.
    """
    def util(chart, i, j, nt) :
        curr = chart[(i, j)][nt]
        if type(curr) is str :
            # Reached terminal
            return (nt, curr)
        else :
            # Yet to reach terminal
            left = curr[0]
            right = curr[1]
            return (nt, get_tree(chart, left[1], left[2], left[0]), get_tree(chart, right[1], right[2], right[0]))
    answer = util(chart, i, j, nt)
    return answer

if __name__ == "__main__":
    with open('atis3.pcfg','r') as grammar_file: 
        grammar = Pcfg(grammar_file) 
        parser = CkyParser(grammar)

        # IN
        in_toks = ['flights', 'from','miami', 'to', 'cleveland','.'] 
        # NOT IN
        not_in_toks = ['miami', 'flights','cleveland', 'from', 'to','.']
        print("Is ['flights', 'from','miami', 'to', 'cleveland','.'] present in language?\n", parser.is_in_language(in_toks), "\n")
        print("Is ['miami', 'flights','cleveland', 'from', 'to','.'] present in language?\n", parser.is_in_language(not_in_toks), "\n")

        table,probs = parser.parse_with_backpointers(in_toks)
        assert check_table_format(table)
        assert check_probs_format(probs)

        print("Parse Tree :\n", get_tree(table, 0, len(in_toks), grammar.startsymbol))