
#!/usr/bin/env python
#import bla




class Character():
    def __init__(self, label):
        self.label = label

    def printLabel(self):
        print(self.label) 

    def equal(self, char):
        return self.label == char.label


class Word():
    def __init__(self, input_list):
        self.list = input_list

    def isTerminal(self):
        pass

    def printWord(self):
        for char in self.list:
            char.printLabel()

    def lenWord(self):
        return len(self.list)

    def at(self, index):
        return self.list[index]

    #def equal(self, word):
    #    for i in range(self.list):

    

class ProductionRule():
    def __init__(self, input_word, output_word):
        self.input_word = input_word
        self.output_word = output_word

    def applyProductionRule(self, start_word):

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

        if not word_found:
            return None

        new_word_list = []

        # Before edit
        for i in range(start_index):
            new_word_list.append(start_word.at(i))

        # During edit
        for i in range(self.output_word.lenWord()):
            new_word_list.append(self.output_word.at(i))

        # After edit
        for i in range(end_index + 1, start_word.lenWord()):
            new_word_list.append(start_word.at(i))

        new_word = Word(new_word_list)

        return new_word


class CFG():
    def __init__(self):

        # Generate a grammar
        self.grammar = self.generateGrammar()

        # Print word
        self.printWords()
    
    def generateGrammar(self):

        # Create empty production rule list
        production_rule_list = []

        # Define input and output words to define a production rule, and add the list
        #input_word = Word([Character("A"), Character("b")])
        input_word = Word([Character("S")])
        output_word = Word([Character("a"), Character("b"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        return production_rule_list

    def printWords(self):

        # Need an input word
        start_word = Word([Character("S")])

        # Apply production rule
        output_word = self.grammar[0].applyProductionRule(start_word)

        # print word
        if output_word:
            output_word.printWord()

if __name__ == "__main__":

    # Execute only if run as a script
    
    cfg = CFG()