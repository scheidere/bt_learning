
#!/usr/bin/env python
#import bla




class Character():
    def __init__(self, label):
        self.label = label

    def printLabel(self):
        print(self.label + " "), 

    def equal(self, char):
        return self.label == char.label

    def toString(self):
        return self.label


class Word():
    def __init__(self, input_list):
        self.list = input_list

    def isTerminal(self):
        pass

    def printWord(self):
        for char in self.list:
            char.printLabel()
        print("")

    def lenWord(self):
        return len(self.list)

    def at(self, index):
        return self.list[index]

    def equal(self, word):
        # Check if words are same length
        if len(self.list) != word.lenWord():
            return False

        # Check if all characters are the same in same length words
        else:
            for i in range(len(self.list)):
                if not self.list[i].equal(word.at(i)): #might need to do .at(i) for word?
                    return False

        return True

    def toString(self):
        str_list = []
        for char in self.list:
            str_list.append(char.toString())
        return " ".join(str_list)

    def createBT(self):        
        
        nodes_worklist = []
        
        for i in range(len(self.list)-1):

            char = self.list[i]
            next_char = self.list[i+1]
        
            node = None

            # Determine the kind of node char is
            if char.equal(Character("?")):
                node = Fallback()
            if char.equal(Character("->")):
                node = Sequence()
            '''
            if char.equal(Character("||")):
                arguments = ??? # Number of children parallel node has
                node = Parallel(int(arguments[0]))
                self.num_child = int(arguments[0])
            '''
            if char.equal(Character("()")):
                node_label = "condition" # Will be the text of the specific condition node
                node = Condition(node_label)
                self.node_text = node_label
            if char.equal(Character("[]")):
                node_label = "action" # Will be the text of the specific action node
                node = Action(node_label)
                self.node_text = node_label
                self.active_ids[node_label] = 0


            # Check if it is the root node, and if so add to list
            if self.root == None:
                self.root = node
                nodes_worklist.append(node)
                continue

            # Check for "(" after a node character, denoting the latter is a parent node
            if next_char.equal(Character("(")):
                # Current node (char) is a child of current parent but also a parent itself
                # Add it as a child to its parent
                parent.add_child(node)
                # Add it to the worklist so its children can be added subsequently
                nodes_worklist.append(node)
                parent = nodes_worklist[-1]
                
            elif char.equal(Character(")")):
                # Done with children of most recent parent
                nodes_worklist.pop()
                parent = nodes_worklist[-1]
                
            elif not char.equal(Character("(")):
                # Remember each child node of current parent
                parent.add_child(node)    
    

class ProductionRule():
    def __init__(self, input_word, output_word):
        self.input_word = input_word
        self.output_word = output_word

    def applyProductionRule(self, start_word):

        # Initialize list for found word/char within word indices
        index_pair_list = []

        # Find insert index
        word_found = False
        for i in range(start_word.lenWord() - self.input_word.lenWord() + 1):
            flag = True
            for j in range(self.input_word.lenWord()):
                if not start_word.at(i+j).equal(self.input_word.at(j)):
                    flag = False
                    break
            if flag:
                word_found = True
                start_index = i
                end_index = i + self.input_word.lenWord() - 1
                index_pair_list.append((start_index,end_index))

        '''
        if not word_found:
            return None 
        '''

        new_word_list = []

        for index_pair in index_pair_list:

            start_index = index_pair[0]
            end_index = index_pair[1]

            new_char_list = []

            # Before edit
            for i in range(start_index):
                new_char_list.append(start_word.at(i))

            # During edit
            for i in range(self.output_word.lenWord()):
                new_char_list.append(self.output_word.at(i))

            # After edit
            for i in range(end_index + 1, start_word.lenWord()):
                new_char_list.append(start_word.at(i))

            new_word = Word(new_char_list)
            new_word_list.append(new_word)

        return new_word_list

    def printProductionRule(self):
        input_word_string = self.input_word.toString()
        output_word_string = self.output_word.toString()
        print_string = input_word_string + " -> " + output_word_string
        print(print_string)


class CFG():
    def __init__(self):

        # Generate a grammar
        self.grammar = self.generateGrammar()

        # Print word
        #self.printWord()

        # Print all words
        self.printAllTerminalWords(4)
    
    def generateGrammar(self):

        # Create empty production rule list
        production_rule_list = []

        # Define input and output words to define a production rule, and add the list
        '''
        input_word = Word([Character("S")])
        output_word = Word([Character("a"), Character("b"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        '''
        input_word = Word([Character("A")])
        output_word = Word([Character("a")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        

        input_word = Word([Character("a"), Character("B")])
        output_word = Word([Character("a"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        
        input_word = Word([Character("B")])
        output_word = Word([Character("b")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("A"), Character("B")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("A"), Character("B")])
        output_word = Word([Character("b"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        '''
        input_word = Word([Character("S")])
        output_word = Word([Character("("), Character("S"), Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("S"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("("), Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        '''
        # test
        input_word = Word([Character("S")])
        output_word = Word([Character("->")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("?")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("->")])
        output_word = Word([Character("execution")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("->")])
        output_word = Word([Character("S"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("->")])
        output_word = Word([Character("->"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("?")])
        output_word = Word([Character("execution")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("?")])
        output_word = Word([Character("S"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("?")])
        output_word = Word([Character("?"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("execution")])
        output_word = Word([Character("condition"), Character("action")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        #print(production_rule_list)
        '''
        '''
        # Word = entire tree

        input_word = Word([Character("S")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("A"),Character("("),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        '''
        #input_word = Word([Character("tree")])
        #output_word = Word([Character("A")])
        #production_rule = ProductionRule(input_word, output_word)
        #production_rule_list.append(production_rule)
        '''
        input_word = Word([Character("children")])
        output_word = Word([Character("A")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("A"),Character("children")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        
        # Behavior Tree Production Rules
        input_word = Word([Character("S")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("?"),Character("("),Character("A"),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("->"),Character("("),Character("A"),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("||"),Character("("),Character("A"),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("A"),Character("children")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("A")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("A")])
        output_word = Word([Character("[]")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("A")])
        output_word = Word([Character("()")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("A")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        


        return production_rule_list

    def printWord(self):

        # Need an input word
        start_word = Word([Character("S")])

        # Apply production rules
        all_rules_tried = False
        while not all_rules_tried:
            no_outputs = False
            for i in range(len(self.grammar)):
                output_word_list = self.grammar[i].applyProductionRule(start_word)

                if len(output_word_list) != 0:
                    no_outputs = True
                    start_word = output_word_list[0]
                    print("Applied rule " + str(i))

                    # print word
                    start_word.printWord()
                    break
            if not no_outputs:
                all_rules_tried = True

    def printAllWords(self):

        # Need the same input word
        start_word = Word([Character("S")])

        # Define word list
        current_list = []

        # Add first word to list
        current_list.append(start_word)

        # Apply production rules
        all_rules_tried = False
        while not all_rules_tried:
            new_list = []
            no_outputs = True
            for i in range(len(current_list)):
                for j in range(len(self.grammar)):
                    output_word_list = self.grammar[j].applyProductionRule(current_list[i])

                    for output_word in output_word_list:
                    #if output_word:
                        no_outputs = False
                        #if output_word not in new_list:
                        duplicate_found = False
                        for word in new_list:
                            if output_word.equal(word):
                                duplicate_found = True
                        if not duplicate_found:        
                            new_list.append(output_word)
                            #print("Applied rule " + str(j))

                            # print word
                            output_word.printWord()
                 
            
            current_list = new_list


            if no_outputs:
                all_rules_tried = True

    def printAllTerminalWords(self, max_depth):

        # Need the same input word
        #start_word = Word([Character("a"), Character("B"), Character("a"), Character("B")])
        start_word = Word([Character("S")])

        # Define word list
        current_list = []

        # Define terminal word list
        terminal_list = []

        # Add first word to list
        current_list.append(start_word)

        # Apply production rules
        all_rules_tried = False
        depth = 0
        while not all_rules_tried and depth < max_depth:
            new_list = []
            no_outputs = True
            for i in range(len(current_list)):
                no_output = True
                for j in range(len(self.grammar)):
                    output_word_list = self.grammar[j].applyProductionRule(current_list[i]) #output_word is now a list

                    for output_word in output_word_list:
                    #if output_word: #removed this because if output_word = None, never appended to output_word_list
                        no_outputs = False
                        no_output = False
                        #if output_word not in new_list:
                        duplicate_found = False
                        for word in new_list:
                            if output_word.equal(word):
                                duplicate_found = True
                        if not duplicate_found:        
                            new_list.append(output_word)
                            #print("Applied rule " + str(j))

                            # print word
                            output_word.printWord()

                if no_output:
                    terminal_list.append(current_list[i])
                    #current_list[i].printWord()
                 
            print("=======")
            current_list = new_list
            depth += 1

            if no_outputs:
                all_rules_tried = True

    def applyAllProductionRules(self, input_word):
        '''
        Return list of all child words of the input word
        '''

        # print("applyAllProductionRules")
        # print("input word: ")
        # input_word.printWord()

        child_words = []
        for i in range(len(self.grammar)):
            output_word_list = self.grammar[i].applyProductionRule(input_word) 

            # print("applying production rule: ")
            # self.grammar[i].printProductionRule()

            # print("generates words: ")
            # for w in output_word_list:
            #     w.printWord()

            # Check if word in output_word_list already in child_words
            for output_word in output_word_list:
                # If output_word not in child_words:
                duplicate_found = False
                for word in child_words:
                    if output_word.equal(word):
                        duplicate_found = True
                if not duplicate_found:        
                    child_words.append(output_word)
            

        return child_words




             

if __name__ == "__main__":

    # Execute only if run as a script
    
    cfg = CFG()

    test = Word()

    test.createBT()