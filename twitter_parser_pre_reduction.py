#this is a class for splitting tweet hastags and or usernames
import re
import htmlentitydefs
from nltk.stem.porter import PorterStemmer
import HTMLParser
from copy import deepcopy


#########
#list of regexes for shortening words: looooovvvvvveeeeeeee -> looovvveee

#############################
#components of the emoticons#
#############################
#not sign sensitive
hat = r"[<>]"
eyes = r"[:;=8]"
nose = r"[\-~oO\*\^\']"
#these are sign sensitive
happy_mouth_s = r"[\)\]\}>dDpP3]" #standard
sad_mouth_s = r"[\(\[\{<]"        #standard
suprised_mouth_s = r"[oO\$]"      #standard
happy_mouth_r = r"[\(\[\{<dpP3]"  #reversed
sad_mouth_r = r"[\)\]\}>]"        #reversed
suprised_mouth_r = r"[oO\$D]"     #reversed
#not sign sensitive
angry_mouth = r"[\\/@]"

#general form for the emoticons of both signs
#these have capture groups since they are checked explicitly in another function
standard_emoticon = r"%s?%s%s?(?:(%s)|(%s)|(%s)|(%s))" % (hat, eyes, nose, happy_mouth_s, sad_mouth_s, angry_mouth, suprised_mouth_s)
reversed_emoticon = r"(?:(%s)|(%s)|(%s)|(%s))%s?%s%s?" % (happy_mouth_r, sad_mouth_r, angry_mouth, suprised_mouth_r, nose, eyes, hat)
#sign ignorant version with non-capturing
standard_emoticon_nc = r"%s?%s%s?(?:%s|%s|%s|%s)" % (hat, eyes, nose, happy_mouth_s, sad_mouth_s, angry_mouth, suprised_mouth_s)
reversed_emoticon_nc = r"(?:%s|%s|%s|%s)%s?%s%s?" % (happy_mouth_r, sad_mouth_r, angry_mouth, suprised_mouth_r, nose, eyes, hat)
emoticon = r"(?:%s|%s)" % (standard_emoticon_nc, reversed_emoticon_nc)


###################
#other tokens used#
###################
phone_num = r"(?:(?:\+?[01][\-\s.]*)?(?:[\(]?\d{3}[\-\s.\)]*)?\d{3}[\-\s.]*\d{4})"
heart = r"<3"
html = r"<[^>]+>"
email = r"(?:[a-z0-9\-\.]+@[a-z0-9\-\.]+\.[a-z]{2,3})"
website = r"(?:(?:https?://)?(?:www\.)?[a-z0-9\-]+\.[a-z]{2,3}(?:/[^\s]*)?)"
handle = r"(?:@[\w_]+)"
hashtag = r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)"
time = r"(?:\d{1,2}:\d{1,2}(?::\d{1,2})?)"
date_num = r"(?:\d{1,2}[/\-\s\\]\d{1,2}(?:[/\-\s\\]\d{1,4})?)"
date_alpha = r"(?:(?:jan|feb|mar|apr|aug|sep|oct|nov|dec)[a-z]{0,6}|(?:jun|jul)[a-z]{0,1}|may)(?:[/\-\s\\]\d{1,2})(?:[/\-\s\\]\d{2,4})?"
num_alpha = r"(?:[a-z0-9\-]*(?:(?:[a-z]\-?[0-9])|(?:[0-9]\-?[a-z]))[a-z0-9\-]*)"
num = r"(?:[0-9][0-9,]*\.?[0-9]*)"
words_et_al = r"(?:[a-z']+)|(?:[\w_]+)|(?:\.(?:\s*\.){1,})|(?:\S)"
    #this version will not split on - or _ but this one will:
    #words_et_al = r"(?:[a-z][a-z'\-_]+[a-z])|(?:[\w_]+)|(?:\.(?:\s*\.){1,})|(?:\S)"

#these are not used in the regex for parsing but they are used for creating special tokens
#these are not needed in parsing since the last step is a simple word and leftover/whitespace tokenizer
num_alpha_other = r"(?=.*[a-z])(?=.*[0-9])(?=.*[^a-z0-9]).*"
units=r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)"
tens = r"(?:twent|thirt|fort|fift|sixt|sevent|eight|ninet)[a-z]{1,3}"
scales = r"(?:hundred|thousand|million)[a-z]{0,1}"

#components of the tokenizer:
#order matters here and this seems to work fine
regex_strings = (phone_num, emoticon, heart, html, email, website, handle, 
                 hashtag, time, date_num, date_alpha, num_alpha, num, words_et_al)

####################################
# This is the core tokenizing regex#
####################################
word_re = re.compile(r"""(%s)""" % "|".join(regex_strings), re.VERBOSE | re.I | re.UNICODE)

#the emoticon string gets its own regex so that we can preserve case for them as needed:
emoticon_re = re.compile(regex_strings[1], re.VERBOSE | re.I | re.UNICODE)

# These are for regularizing HTML entities to Unicode:
html_entity_digit_re = re.compile(r"&#\d+;")
html_entity_alpha_re = re.compile(r"&\w+;")
amp = "&amp;"

################################################
#class containing all the tokenization features#
################################################
class Tokenizer:
    def __init__(self, preserve_case=False):
        self.preserve_case = preserve_case

    def tokenize(self, s):
        """
        Argument: s -- any string or unicode object
        Value: a tokenize list of strings; concatenating this list returns the original string if preserve_case=False
        """        
        # Try to ensure unicode:
        try:
            s = unicode(s)
        except UnicodeDecodeError:
            s = str(s).encode('string_escape')
            s = unicode(s)
        # Fix HTML character entitites:
        s = self.__html2unicode(s)
        # Tokenize:
        words = word_re.findall(s)
        # Possible alter the case, but avoid changing emoticons like :D into :d:
        if not self.preserve_case:            
            words = map((lambda x : x if emoticon_re.search(x) else x.lower()), words)            
        return words

    def __html2unicode(self, s):
        """
        Internal metod that seeks to replace all the HTML entities in
        s with their corresponding unicode characters.
        """
        # First the digits:
        ents = set(html_entity_digit_re.findall(s))
        if len(ents) > 0:
            for ent in ents:
                entnum = ent[2:-1]
                try:
                    entnum = int(entnum)
                    s = s.replace(ent, unichr(entnum))
                except:
                    pass
        # Now the alpha versions:
        ents = set(html_entity_alpha_re.findall(s))
        ents = filter((lambda x : x != amp), ents)
        for ent in ents:
            entname = ent[1:-1]
            try:            
                s = s.replace(ent, unichr(htmlentitydefs.name2codepoint[entname]))
            except:
                pass                    
            s = s.replace(amp, " and ")
        return s

    def special_tokens(self, split_tweet):
        
        split_tweet_mapped = []
        for token in split_tweet:
            token = re.sub(r'^' + phone_num + r'$', "|~phone_num~|", token)
            token = re.sub(r'^' + heart + r'$', "|~heart~|", token)
            token = re.sub(r'^' + email + r'$', "|~email~|", token)
            token = re.sub(r'^' + website + r'$', "|~website~|", token)
            token = re.sub(r'^' + time + r'$', "|~time~|", token)
            token = re.sub(r'^' + date_num + r'$', "|~date~|", token)
            token = re.sub(r'^' + date_alpha + r'$', "|~date~|", token)
            token = re.sub(r'^' + num_alpha_other + r'&', "|~num_alpha_other~|", token)
            token = re.sub(r'^' + num_alpha + r'$', "|~num_alpha~|", token)
            token = re.sub(r'^' + num + r'$', "|~num~|", token)
            token = re.sub(r'^' + units + r'$', "|~units~|", token)
            token = re.sub(r'^' + tens + r'$', "|~tens~|", token)
            token = re.sub(r'^' + scales + r'$', "|~scales~|", token)
        
            split_tweet_mapped.append(token)
    
        return split_tweet_mapped
        
    def classify_emoticons(self, split_tweet):         
        #loop over tokens and replace
        split_tweet_mapped = []
        for token in split_tweet:
            match = re.search(r'^' + standard_emoticon + r'$', token)
            if not match:
                match = re.search(r'^' + reversed_emoticon + r'$', token)
            if match:
                if match.group(1):
                    split_tweet_mapped.append("|~happy~|")
                elif match.group(2):
                    split_tweet_mapped.append("|~sad~|")
                elif match.group(3):
                    split_tweet_mapped.append("|~angry~|")
                elif match.group(4):
                    split_tweet_mapped.append("|~suprised~|")
            else:
                split_tweet_mapped.append(token)
            
        return split_tweet_mapped
        
        
    #def shorten_word(self, tweet):
        
        #alphabet = "abcdefghijklmnopqrstuvwxyz"
        #for letter in alphabet:
        #r"%s{3}%s+"