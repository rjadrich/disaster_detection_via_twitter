#this is a class for splitting tweet hastags and or usernames
import re
import htmlentitydefs

######################################################################
# The following strings are components in the regular expression
# that is used for tokenizing. It's important that phone_number
# appears first in the final regex (since it can contain whitespace).
# It also could matter that tags comes after emoticons, due to the
# possibility of having text like
#
#     <:| and some text >:)
#
# Most imporatantly, the final element should always be last, since it
# does a last ditch whitespace-based tokenization of whatever is left.

# This particular element is used in a couple ways, so we define it
# with a name:

#common emoticons
emoticon_string = r"""
    (?:
      [<>]?
      [:;=8]                     # eyes
      [\-~oO\*\']?                 # optional nose
      [\)\]\(\[dDpP3/\}\{@\|\\<>oO\$] # mouth      
      |
      [\)\]\(\[dDpP3/\}\{@\|\\<>oO\$] # mouth
      [\-~oO\*\']?                 # optional nose
      [:;=8]                     # eyes
      [<>]?
    )"""

#other tokens used for parsing tweet
heart = r"""<3"""
phone_num = r"""(?:(?:\+?[01][\-\s.]*)?(?:[\(]?\d{3}[\-\s.\)]*)?\d{3}[\-\s.]*\d{4})"""
html = r"""<[^>]+>"""
email = r'''(?:[a-z0-9\-\.]+@[a-z0-9\-\.]+\.[a-z]{2,3})'''
handle = r"""(?:@[\w_]+)"""
hashtag = r"""(?:\#+[\w_]+[\w\'_\-]*[\w_]+)"""
time = r"""(?:\d{1,2}:\d{1,2}(?::\d{1,2})?)"""
date = r"""(?:\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{1,4})?)"""
num_alpha = """(?:[a-z0-9]*(?:(?:[a-z][0-9])|(?:[0-9][a-z]))[a-z0-9]*)"""
num = r"""(?:[0-9][0-9,]*\.?[0-9]*)"""
website = r"""(?:(?:http://|https://)?(?:www\.)?[a-z0-9\-]+\.[a-z]{2,3}(?:/[^\s]*)?)"""
words_et_al = r"""(?:[a-z][a-z'\-_]+[a-z])|(?:[\w_]+)|(?:\.(?:\s*\.){1,})|(?:\S)"""

#these are not used in the regex for parsing but they are for creating special tokens
num_alpha_other = r'(?=.*[a-z])(?=.*[0-9])(?=.*[^a-z0-9]).*'
units=r'''(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)'''
tens = r'(?:twent|thirt|fort|fift|sixt|sevent|eight|ninet)[a-z]{1,3}'
scales = r'(?:hundred|thousand|million)[a-z]{0,1}'

# The components of the tokenizer:
regex_strings = (phone_num, emoticon_string, heart, html, email, handle, 
                 hashtag, time, date, num_alpha, num, website, words_et_al)

######################################################################
# This is the core tokenizing regex:
    
word_re = re.compile(r"""(%s)""" % "|".join(regex_strings), re.VERBOSE | re.I | re.UNICODE)

# The emoticon string gets its own regex so that we can preserve case for them as needed:
emoticon_re = re.compile(regex_strings[1], re.VERBOSE | re.I | re.UNICODE)

# These are for regularizing HTML entities to Unicode:
html_entity_digit_re = re.compile(r"&#\d+;")
html_entity_alpha_re = re.compile(r"&\w+;")
amp = "&amp;"

######################################################################

class Tokenizer:
    def __init__(self, preserve_case=False):
        self.preserve_case = preserve_case

    def tokenize(self, s):
        """
        Argument: s -- any string or unicode object
        Value: a tokenize list of strings; conatenating this list returns the original string if preserve_case=False
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
            token = re.sub(r'^' + heart + r'$', "|~heart~|", token)
            token = re.sub(r'^' + phone_num + r'$', "|~phone_num~|", token)
            token = re.sub(r'^' + time + r'$', "|~time~|", token)
            token = re.sub(r'^' + date + r'$', "|~date~|", token)
            token = re.sub(r'^' + num + r'$', "|~num~|", token)
            token = re.sub(r'^' + num_alpha + r'$', "|~num_alpha~|", token)
            token = re.sub(r'^' + email + r'$', "|~email~|", token)
            token = re.sub(r'^' + website + r'$', "|~website~|", token)
            token = re.sub(r'^' + num_alpha_other + r'&', "|~num_alpha_other~|", token)
            token = re.sub(r'^' + units + r'$', "|~units~|", token)
            token = re.sub(r'^' + tens + r'$', "|~tens~|", token)
            token = re.sub(r'^' + scales + r'$', "|~scales~|", token)
        
            split_tweet_mapped.append(token)
    
        return split_tweet_mapped
        
    def classify_emoticons(self, split_tweet):    
        #regular expressions for the various special tokens
        standard_emoticon = r'^[<>]?[:;=8][\-~oO\*\^\']?(?:([\)\]\}>dDpP3])|([\(\[\{<])|([\\/@])|([oO\$]))$'
        reversed_emoticon = r'^(?:([\(\[\{<dDpP3])|([\)\]\}>])|([\\/@])|([oO\$]))[\-~oO\*\^\']?[:;=8][<>]?$'
        #twitter_emojis = 
     
        #loop over tokens and replace
        split_tweet_mapped = []
        for token in split_tweet:
            match = re.search(standard_emoticon, token)
            if not match:
                match = re.search(reversed_emoticon, token)
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