from gensim import corpora, models
from collections import defaultdict
import string
import pandas as pd
from numpy import maximum

class latent_semantic_indexer:  

    def make_dictionary_and_corpus(self, dictionary_df, corpus_df, min_word_count = 1):
    
        #establish the texts
        texts = dictionary_df
        
        #check how frequently a given word appears and remove it if only one occurrence
        frequency = defaultdict(int)
        for text in texts:
            for token in text:
                frequency[token] += 1
        texts = [[token for token in text if frequency[token] > min_word_count] for text in texts]
    
        #create a gensim dictionary
        self.dictionary = corpora.Dictionary(texts)
    
        #create a new texts with all words restored
        texts = corpus_df    
    
        #create the bag of words corpus
        self.corpus = [self.dictionary.doc2bow(text) for text in texts]
    
        #create a tfidf wrapper and convert the corpus to a tfidf format
        self.tfidf = models.TfidfModel(self.corpus)
        self.corpus_tfidf = self.tfidf[self.corpus]
        

    #cleans up data for use in dataframe
    def remove_doc_label(self, doc):
        cleaned_doc = []
        for element in doc:
            cleaned_doc.append(element[1])
        return cleaned_doc
    

    def latent_semantic_indexing(self, df, num_topics, power_iters = 10):
        #create a lsi wrapper around the tfidf wrapper
        self.lsi = models.LsiModel(self.corpus_tfidf, id2word=self.dictionary, num_topics = num_topics, power_iters = power_iters)
        self.corpus_lsi = self.lsi[self.corpus_tfidf]
        
        #create the features for a new dataframe
        features = []
        for doc in self.corpus_lsi:
            features.append(self.remove_doc_label(doc))
        
        #create a new dataframe with the features
        df_features = pd.DataFrame(data = features)
    
        #create a merged dataframe from the input (the indicies should match since I reset them earlier on)
        df_merged = pd.concat([df, df_features], axis=1)
        
        #create index for similarity query
        self.index = similarities.MatrixSimilarity(self.corpus_lsi, num_features = num_topics)
        
        return df_merged.fillna(0)
            
    def fetch_topics(self, num_topics = 10, num_words = 10):
        return self.lsi.print_topics(num_topics, num_words = num_words)
    
    def make_lsi_vector(self, text):
        
        #convert tokenized from BOW->TFIDF->LSI
        vector_bow = self.dictionary.doc2bow(text)
        vector_tfidf = self.tfidf[vector_bow]
        vector_lsi = self.lsi[vector_tfidf]
        
        return vector_lsi    
    
    def generate_similarity(self, df, texts):
        
        #generate LSI vector and index it against the whole corpus and apply similarity result to dataframe
        
        df["Similarity"] = [0.0 for num in range(len(df))]
        for text in texts:
            vector_lsi = self.make_lsi_vector(text)
            sims = self.index[vector_lsi]
            df["Similarity"] = df["Similarity"] + sims
        
        df["Similarity"] = df["Similarity"] / len(texts)

        return df
    
    