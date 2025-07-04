from nltk.corpus import wordnet
import pandas as pd

def get_wordnet_entries(word_lst):
    """
    Returns a DataFrame of wordnet entries for all words in word_lst
    """
    base_words = []
    synset_id = []
    gloss = []
    example = []

    for word in word_lst:
        result = wordnet.synsets(word)
        
        if not result:
            print('No found: ', word)
            continue

        for item in result:
            example_lst = item.examples()

            # if len(example_lst) <= 0: # do not include sense if it has no example sentences
            #     continue

            if len(example_lst) < 2: # do not include sense if it has less than 2 example sentences
                continue

            base_words.append(word)
            synset_id.append(item.name())
            gloss.append(item.definition())
            example.append(" | ".join(example_lst))

    data = {'word': base_words, 'synset_id': synset_id, 'gloss': gloss, 'eng_text': example}
    df = pd.DataFrame(data=data)

    return df