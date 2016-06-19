import re
from numpy import log
from nltk.corpus import brown

class Word_Reduction:
    
    def __init__(self, use_brown = True):
        #store our freq count for each word
        self.frequencies = {}
        self.mappings = {}
        #build the regex to check for one or more
        self.three_or_more_combos = [(r"%s{3}%s*" % (letter, letter)) for letter in "abcdefghijklmnopqrstuvwxyz"]
        self.three_or_more_re = r"(" + r"|".join(self.three_or_more_combos) + r")" 
        #build the regex to extract a single letter even if repeated
        self.one_or_more_combos = [(r"%s+" % letter) for letter in "abcdefghijklmnopqrstuvwxyz"]
        self.one_or_more_re = r"(" + r"|".join(self.one_or_more_combos) + r")"
        
        #default word library employed unless user says otherwise
        if use_brown:
            modified_brown = [word.lower() for word in brown.words() 
                  if (len(word) > 2 or word.lower() 
                      in ("a i an as at be bi by do he hi if in is it " +
                      "me my no of or on so to up us we").split(" "))]
            self.make_freq(modified_brown)
            self.make_mappings()
        
    #function to check if word is a word and has three or more letter repeats
    def is_reducible(self, word):
        return (word.isalpha() and bool(re.findall(self.three_or_more_re, word)))

    #function to return reduced representation for mapping
    def reduce_letters(self, word):
        letter_list = [letters[0] for letters in re.findall(self.one_or_more_re, word)]
        return "".join(letter_list)
    
    #generates the freq count for each word by sending in the word bank
    def make_freq(self, word_bank):
        #make the frequency count
        word_bank_L = [word for word in word_bank]
        for token in word_bank_L:               
            if token in self.frequencies:
                self.frequencies[token] = self.frequencies[token] + 1.0
            elif token.isalpha():
                self.frequencies[token] = 1.0
                
    #creates the mappings between simplified words and most probable full word
    def make_mappings(self):
        #make the reduced word to full word mapping
        for token in self.frequencies:
            token_reduced = self.reduce_letters(token)
            if token_reduced in self.mappings:
                current_count = log(self.frequencies[self.mappings[token_reduced]])
                new_count = log(self.frequencies[token])
                if new_count > current_count:
                    self.mappings[token_reduced] = token
            else:
                self.mappings[token_reduced] = token
    
    #tries to find a mapping and if so returns True and the reduced word
    def find_mapping(self, word):
        if self.is_reducible(word):
            word_reduced = self.reduce_letters(word)
            if word_reduced in self.mappings:
                return (True, self.mappings[word_reduced])
            else:
                return (False, word)
        else:
            return (False, word)