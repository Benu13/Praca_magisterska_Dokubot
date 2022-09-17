# Logic

from Dokubot.LoadModels import Dokubot


class Tree:
    def __init__(self, logic, leafs):
        #logic - Logic token from essence
        self.logic = logic.logic
        self.logic_token = logic
        self.leafs = leafs
        self.simplified = []

    def simplify(self):
        for leaf in self.leafs:
            if isinstance(leaf, Tree):
                leaf.simplify()
                if self.logic == leaf.logic:
                    self.simplified.extend(leaf.simplified)
                else:
                    self.simplified.append(leaf)
            else:
                self.simplified.append(leaf)

    def print_tree(self):
        print(self.logic)
        flag = 0
        for leaf in self.leafs:
            if isinstance(leaf, Tree):
                print(leaf.logic, end=' ')
            else:
                print(leaf, end=' ')
        print('\n')
        for leaf in self.leafs:
            if isinstance(leaf, Tree):
                leaf.print_tree()

    def print_simp_tree(self):
        print(self.logic)
        flag = 0
        for leaf in self.simplified:
            if isinstance(leaf, Tree):
                print(leaf.logic, end=' ')
            else:
                print(leaf, end=' ')
        print('\n')
        for leaf in self.simplified:
            if isinstance(leaf, Tree):
                leaf.print_tree()

    def represent_list(self):
        string = ['(']
        op = len(self.simplified) - 1
        num = 0

        for i in range(len(self.simplified)):
            if isinstance(self.simplified[i], Tree):
                string.extend(self.simplified[i].represent_list())

                if num < op:
                    string.append(self.logic_token)
                    num += 1
            else:
                string.append(self.simplified[i])
                if num < op:
                    string.append(self.logic_token)
                    num += 1
        string.append(')')

        return string

    def represent_string(self):
        string = '('
        op = len(self.simplified) - 1
        num = 0

        for i in range(len(self.simplified)):
            if isinstance(self.simplified[i], Tree):
                string += self.simplified[i].represent_string()

                if num < op:
                    string += ' ' + self.logic_token.logic_pl + ' '
                    num += 1
            else:
                string += self.simplified[i].word
                if num < op:
                    string += ' ' + self.logic_token.logic_pl + ' '
                    num += 1
        string += ')'

        return string


class LogicHandler:
    def __init__(self):

        self.UNI_flag = False
        self.UNI_tokens = []

    def solve(self, tokens, logic):
        self.UNI_flag = False
        self.UNI_tokens = []

        if not logic:
            return  ("CL", tokens)

        if not tokens:
            return  ("NO", ) #No keys flag

        ambigious, logic = self.check_logic_ambiguity(logic)
        if ambigious:
            if self.UNI_flag:
                return ("UNI", self.UNI_tokens) # raise UNIDENTIFIED KEY (UNI_K) logic token flag
            else:
                # try to unravel logic operators
                combinations = self.get_combinations(len(tokens))
                trees = self.get_trees(combinations, logic, tokens)
                reduced_comb = self.reduce_similar_trees(trees)
                return ("SCL", reduced_comb) # raise select correct logic flag

        return ("CL", self.connect_logic(tokens, logic)) # raise all clear flag

    def connect_logic(self, keys, logic):
        key_part = []
        for i in range(len(keys) - 1):
            key_part.append(keys[i])
            key_part.append(logic[i])
        key_part.append(keys[-1])
        return key_part

    def check_logic_ambiguity(self, logic):
        # check if operators are unambigous

        if len(set([lo.logic for lo in logic])) == 1:
            if logic[0].logic == 'NEU':
                logic = self.disambiguate_operators(logic)
            if logic[0].logic == 'UNI':
                self.UNI_flag = True
                self.UNI_tokens = [i for i in range(len(logic))]
                return True, logic

            return False, logic
        else:
            logic = self.disambiguate_operators(logic)
            if len(set([lo.logic for lo in logic])) == 1:
                return False, logic
            else:
                return True, logic

    def disambiguate_operators(self, logic, alg='backprop', last_operator="AND"):
        if alg == 'FFa':
            # assume comma as and with forward flow
            for i in range(len(logic)):
                if logic[i].logic == 'NEU':
                    logic[i].logic = 'AND'
        elif alg == 'backprop':
            # logic operator backpropagation
            last_op = last_operator
            for i in reversed(range(len(logic))):
                if logic[len(logic)-i-1].logic == 'UNI':
                    self.UNI_flag = True
                    self.UNI_tokens.append(len(logic)-i-1)
                if logic[i].logic == 'NEU':
                    logic[i].logic = last_op
                    logic[i].logic_pl = self.get_logic_pl(last_op)
                else:
                    last_op = logic[i].logic
            return logic

    def get_combinations(self, len_keys):
        expr = [str(i) for i in range(len_keys)]
        combinations = []
        for combination in self.catalan(expr):
            combinations.append(combination)
        return combinations

    def get_trees(self, combinations, logic, keys):
        trees = []
        for combination in combinations:
            lcomb = self.get_listed_combination(combination, logic, keys)
            trees.append(self.build_tree(lcomb)[0])
        return trees

    def reduce_similar_trees(self, trees):
        reduced_comb = []
        reduced_comb_str = []
        for tree in trees:
            tree.simplify()
            tr = tree.represent_list()
            st = tree.represent_string()
            if st not in reduced_comb_str:
                reduced_comb_str.append(st)
                reduced_comb.append((st, tr))
                #reduced_trees.append(tree)

        return reduced_comb

    def get_listed_combination(self, form, logic, keys):
        express = []
        j = 0
        place_after_par = False
        for i in range(len(form) - 1):
            if form[i] not in ['(', ')']:
                express.append(keys[int(form[i])])
            else:
                express.append(form[i])

            if place_after_par:
                if form[i + 1] != ')':
                    express.append(logic[j])
                    place_after_par = False
                    j += 1
            if form[i] not in ['(', ')']:
                if form[i + 1] != ')':
                    express.append(logic[j])
                    j += 1
                else:
                    place_after_par = True

        if form[-1] == ')':
            express.append(form[-1])
        else:
            express.append(keys[int(form[-1])])
        return ['('] + express + [')']

    def build_tree(self, expression):
        reduced = []
        length = len(expression)
        i = 0
        while i < length:
            if expression[i] == '(' and expression[i + 4] == ')':
                tree = Tree(expression[i + 2], [expression[i + 1], expression[i + 3]])
                reduced.append(tree)
                i = i + 5
            else:
                reduced.append(expression[i])
                i += 1
            # print(reduced)

        if len(reduced) > 1:
            reduced = self.build_tree(reduced)

        return reduced

    def catalan(self, exprssion):
        if len(exprssion) == 1:
            yield exprssion[0]
        else:
            first_exprs = []
            last_exprs = list(exprssion)
            while 1 < len(last_exprs):
                first_exprs.append(last_exprs.pop(0))
                for x in self.catalan(first_exprs):
                    if 1 < len(first_exprs):
                        x = '(%s)' % x
                    for y in self.catalan(last_exprs):
                        if 1 < len(last_exprs):
                            y = '(%s)' % y
                        yield '%s%s' % (x, y)

    def get_logic_pl(self, logic):
        if logic == 'OR':
            logic_pl = 'lub'
        elif logic == 'AND':
            logic_pl = 'oraz'
        elif logic == 'AND NOT':
            logic_pl = 'oraz nie'
        elif logic == 'OR NOT':
            logic_pl = 'lub nie'
        else:
            logic_pl = 'nieznany'

        return logic_pl

if __name__ == '__main__':

    config = {
        'OOV_handler_type': 'mimic',
        'correct_misspell': True,
        'spacy_size': 'md',
        'misspell_cor_algorithm': 'lev',
        'spacy_from_path': True,
        'spacy_disable': ["attribute_ruler", "ner", 'tagger', 'parser', 'morphologizer'],
        'paths': {
            'slot_filler_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/slot_filer/slot_mimic/slot_mimic_medium.h5',
            'slot_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_slot.json',
            'choice_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_choice.json',
            'spacy_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/Spacy_md/',
            'mimic_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/mimic/mimic_smol/mimic_smol.h5',
            'char2tok_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/mimic/mimic_smol/char_tokenizer_mimic_smol.json',
            'misspell_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_docs.json'
        }

    }

    Dokubot = Dokubot(config)
    test_test = Dokubot.extract("poleć mi książkę o jeleniach lub i kotach")

    keys = test_test.essence[0]['doc_types']
    logic = test_test.essence[0]['doc_operators']

    a = LogicHandler()
    op = a.solve(keys, logic)
    #kp = a.solve_keys()

    print('a')

'''
    def solve_doc(self, docs, docs_operators):
        self.UNI_flag = False
        self.UNI_tokens = []
        doc_all = False
        doc_pref = []
        doc_pref_logic = []
        
        if not docs_operators:
            return  ("CL_D", doc_all, doc_pref)

        if not docs:
            return  ("NO_D") #No docs flag

        #solve doc logic
        ambigious, doc_pref_logic = self.check_logic_ambiguity(docs_operators)
        if ambigious:
            if self.UNI_flag:
                return ("UNI_D", doc_all, self.UNI_tokens) # raise UNIDENTIFIED DOC (UNI_D) logic token flag
            else:
                # try to unravel logic operators
                combinations = self.get_combinations(len(doc_pref))
                trees = self.get_trees(combinations, doc_pref_logic, doc_pref)
                reduced_comb = self.reduce_similar_trees(trees)
                return ("SCL_D", doc_all, reduced_comb) # raise select correct logic flag
        
        # solve if all in doc_types
        for i in range(len(docs)):
            if docs[i].origin in ['coś', 'czegoś', 'dokument', 'papier']:
                if not doc_all:
                    doc_all = True
                else:
                    pass
            else:
                doc_pref.append(docs[i])
                if i > 0:
                    doc_pref_logic.append(docs_operators[i-1])
        
        return ("CL_D", doc_all, self.connect_logic(doc_pref, doc_pref_logic))  # raise all doc clear flag'''