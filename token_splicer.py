#this is a class for splitting tweet hastags and or usernames
from numpy import log
from copy import deepcopy
from nltk.corpus import brown

class Token_Splicer:

    def __init__(self, use_brown = True):
        self.frequencies = {} #store our freq count for each word
        self.split_sequence_locker = {} #save any unique recursive string split sequences
        
        if use_brown:
            modified_brown = [word.lower() for word in brown.words() 
                  if (len(word) > 2 or word.lower() 
                      in ("a i an as at be bi by do he hi if in is it " +
                      "me my no of or on so to up us we").split(" "))]
            self.make_freq(modified_brown)

    def make_freq(self, word_bank): #generates the freq count for each words by sending in the word bank
        word_bank_L = [word for word in word_bank]
        for token in word_bank_L:               
            if token in self.frequencies:
                self.frequencies[token] = self.frequencies[token] + 1.0
            elif token.isalpha():
                self.frequencies[token] = 1.0
                
    def log_freq(self, token): #returns the log freq to avoid underflow issues
        if token in self.frequencies:
            return log(self.frequencies[token])
        elif token.isalpha():
            return -100000.0 #this really penalizes forming to many random words
        else:
            return 0.0

    def gen_sequence(self, num_splits, splits, max_pos): #recursive function to generate a unique split sequence
        if len(splits) == 0:
            min_split = 1
        else:
            min_split = splits[-1] + 1

        if len(splits) < num_splits:
            for new_split in range(min_split, max_pos + 1):
                splits_out = deepcopy(splits)
                splits_out.append(new_split)
                self.gen_sequence(num_splits, deepcopy(splits_out), max_pos)
        else:
            self.split_sequence_locker[(num_splits, max_pos)].append(splits)
            
    def break_tokens(self, conjoined_tokens, split_sequence): #breaks a conjoined token according to split sequence
        broken_tokens = []
        
        split_h = split_sequence[0]
        broken_tokens.append(conjoined_tokens[:split_h])
        for i in range(0, len(split_sequence) - 1):
            split_l = split_sequence[i]
            split_h = split_sequence[i + 1]
            broken_tokens.append(conjoined_tokens[split_l:split_h])   
        split_l = split_sequence[-1]
        broken_tokens.append(conjoined_tokens[split_l:])
        
        return broken_tokens
          
    def max_prob_split(self, conjoined_tokens, degree): #does the splitting iteratively with desired degree
        
        max_pos = len(conjoined_tokens[0]) - 1
        
        #make list of the iterations to create total breaks
        degree_iterations = [degree for k in range(degree, max_pos, degree)]
        left_over = max_pos - sum(degree_iterations)
        if left_over > 0:
            degree_iterations.append(left_over)
        
        final_broken_tokens = []
        
        for cur_degree in degree_iterations:
        
            max_proba = sum([self.log_freq(token) for token in conjoined_tokens])
            max_broken_tokens = deepcopy(conjoined_tokens)
        
            for num_splits in range(1, cur_degree + 1):
                if (num_splits, max_pos) not in self.split_sequence_locker:
                    self.split_sequence_locker[(num_splits, max_pos)] = []
                    self.gen_sequence(num_splits, [], max_pos)
                
                for split_sequence in self.split_sequence_locker[(num_splits, max_pos)]:
                    broken_tokens = self.break_tokens(conjoined_tokens[0], split_sequence)
                    proba = sum([self.log_freq(token) for token in broken_tokens])
                    if (proba > max_proba):
                        max_proba = proba
                        max_broken_tokens = broken_tokens
            
            probas = [self.log_freq(token) for token in max_broken_tokens]
            min_token_loc = probas.index(min(probas))
            conjoined_tokens = [max_broken_tokens.pop(min_token_loc)]
            for token in max_broken_tokens:
                final_broken_tokens.append(token)
        
        final_broken_tokens.append(conjoined_tokens[0])
                    
        return final_broken_tokens