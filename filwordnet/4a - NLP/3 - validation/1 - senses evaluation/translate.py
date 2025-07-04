# run in cmd on current dir before running jupyter notebook using the same terminal: 
# set GOOGLE_APPLICATION_CREDENTIALS=translate-319807-2956a05ce54d.json
import time
import six
from google.cloud import translate_v2 as translate

def translate_text(source, target, text): # <en> to <tl>, translate this <text>
    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    result = translate_client.translate(text, target_language=target, source_language=source)

    # print(u'Text: {}'.format(result['input']))
    # print(u'Translation: {}'.format(result['translatedText']))
    # print(result)

    return result['translatedText']

def en_to_tl(text):
    return translate_text('en', 'tl', text) # <en> to <tl>, translate this <text>

def tl_to_en(text):
    return translate_text('tl', 'en', text) # <tl> to <en>, translate this <text>

def translate_df(df, mode='en_to_tl', backtranslate=False):
    new_df = df.copy()
    translated_texts = []
    backtranslated_texts = []
    n_rows, n_cols = df.shape
    counter = 0

    if mode == 'en_to_tl':
        target_col = 'eng_text'
        translator = en_to_tl
        if backtranslate:
            backtranslator = tl_to_en
    elif mode == 'tl_to_en':
        target_col = 'fil_text'
        translator = tl_to_en
        if backtranslate:
            backtranslator = en_to_tl

    # Process DataFrame (df)
    for index, row in new_df.iterrows():
        notFinish = True
        while notFinish:
            try:
                translated_text = translator(row[target_col])
                counter += 1
                print(f"Progress: {(counter / n_rows):.2f}")
                print(f'translated_text: {translated_text}')
                translated_texts.append(translated_text)
                notFinish = False
                
                if backtranslate:
                    backtranslated_text = backtranslator(translated_text)
                    backtranslated_texts.append(backtranslated_text)
                    print(f'backtranslated_text: {backtranslated_text}')
                    
            except Exception as e:
                print('exception error: sleeping for 3 seconds...')
                print(e)
                time.sleep(3)
                continue


    if mode == 'en_to_tl':
        new_df['fil_text'] = translated_texts
    elif mode == 'tl_to_en':
        new_df['eng_text'] = translated_texts
    
    if backtranslate:
        new_df['backtranslation'] = backtranslated_texts

    return new_df




