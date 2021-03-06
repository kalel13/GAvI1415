import nltk
from nltk.classify.util import *
from nltk.metrics import *
import webbrowser
import sys
from yattag import Doc, indent
from nltk.corpus import stopwords

# Connessione SQLite3
import sqlite3
conn = sqlite3.connect('tweets.db')

# Creazione della tupla per i tweets positivi estrapolando le frasi dal DB
positive_phrase = conn.execute('SELECT * FROM positive_tweets ORDER BY id')
pos_tweets = []
for row in positive_phrase:
    pos_tweets.append((row[1], 'positive'))
# Test di stampa
#print pos_tweets

# Creazione della tupla per i tweets negativi estrapolando le frasi dal DB
negative_phrase = conn.execute('SELECT * FROM negative_tweets ORDER BY id')
neg_tweets = []
for row in negative_phrase:
    neg_tweets.append((row[1], 'negative'))
# Test di stampa
#print neg_tweets



# Dato un insieme di tweets(training set) ritorna una lista
# contenente solo le parole.
def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
        all_words.extend(words)
    return all_words


# Data una lista di parole, elimina le parole ripetute
# e ritorna una lista ordinata per frequenza di parola.
def get_word_features(wordlist):
    wordlist = nltk.FreqDist(wordlist)
    word_features = wordlist.keys()
    return word_features


# Crea un dizionario che indica per ogni parola contenuta nel training set
# se e presente o meno nel tweet passato in input.
# esempio:
# {love: True, this: True, car: True, hate: False, Concert: False}
def extract_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features


if __name__ == "__main__":
    # Creazione di una lista contenente un array di parole prive di stopwords
    # con accanto la classificazione positivo/negativo
    wnl = nltk.WordNetLemmatizer()

    test_tweets = []
    for (phrase, sentiment) in pos_tweets + neg_tweets:
        tokens = nltk.word_tokenize(phrase)
        for t in tokens:
            if t in stopwords.words('english'):
                tokens.remove(t)
        test_tweets.append((tokens, sentiment))

    # Lista contenente le parole presenti nel training set ordinate per frequenza
    word_features = get_word_features(get_words_in_tweets(test_tweets))

    training_set = nltk.classify.apply_features(extract_features, test_tweets)
    classifier = nltk.NaiveBayesClassifier.train(training_set)

    # Gestire l'input dell'applicazione
    print "Inserire il tweet da valutare"
    tweet = sys.stdin.readline().rstrip("\n")
    tweet.lower()

    tokens = nltk.word_tokenize(tweet)
    #print tokens
    for t in tokens:
        if t in stopwords.words('english'):
            tokens.remove(t)
    #print tokens

    prob_t = classifier.prob_classify(extract_features(tokens))
    sent = prob_t.max()

    #print tweet
    #print "Classificazione:", sent
    #print "Tweet positivo al", round(prob_t.prob('positive'), 2)*100, "%"
    #print "Tweet negativo al", round(prob_t.prob('negative'), 2)*100, "%"

    # Output in XML
    doc, tag, text = Doc().tagtext()

    with tag('classification'):
        with tag('title'):
            text('Machine Learning Sentiment Analysis Application')
        with tag('tweet'):
            with tag('text'):
                text(tweet)
            with tag('sentiment'):
                text('Classification: ' + sent + ' tweet')
            with tag('negative'):
                text('This tweet is negative to')
            with tag('score'):
                text(str(round(prob_t.prob('negative'), 2) * 100) + '%')
            with tag('positive'):
                text('This tweet is positive to')
            with tag('score'):
                text(str(round(prob_t.prob('positive'), 2) * 100) + '%')

    result = indent(
        doc.getvalue(),
        indentation='\t',
        newline='\n'
    )

    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
             '<?xml-stylesheet type="text/css" href="css/classification.css"?>\n'.__add__(result)

    out_file = open("classification.xml", "w")
    out_file.write(result)
    out_file.close()

    import os
    url =  os.path.realpath("classification.xml")
    webbrowser.open_new_tab('file:///'+url)


    print "Inserire il tweet nel DB? [y/n]"
    ins = sys.stdin.readline().lower().rstrip("\n")

    if ins in ['yes', 'y', 'si', 's']:
        print "La classificazione e corretta? [y/n]"
        conf = sys.stdin.readline().lower().rstrip("\n")

        if conf in ['yes', 'y', 'si', 's']:
            if sent == "positive":
                conn.execute('INSERT INTO positive_tweets (text) VALUES ("%s")' % tweet)
            else:
                conn.execute('INSERT INTO negative_tweets (text) VALUES ("%s")' % tweet)
            conn.commit()
        elif conf in ['no', 'n', 'nope']:
            if sent == "positive":
                conn.execute('INSERT INTO negative_tweets (text) VALUES ("%s")' % tweet)
            else:
                conn.execute('INSERT INTO positive_tweets (text) VALUES ("%s")' % tweet)
            conn.commit()
        else:
            print "Scelta errata, il tweet non e stato inserito nel DB."
    else:
        print "Tweet non inserito nel DB."