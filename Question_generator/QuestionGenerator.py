import random
import morfeusz2
import pandas as pd

def find_doc_to_search_word(search_word, doc_types):
    '''
        # select doc_type allowed after specyfic search word( look sentence blocks0
    :param search_word: dict - choosen search word form search word list of dicts
    :param doc_types: list[dict] - list of all doc_types
    :return: doc_type - dict of selected doc type
    '''

    doc_type = random.choice(doc_types)
    while search_word['przypadek'] not in doc_type['dozwolone_po']:
        doc_type = random.choice(doc_types)
    return doc_type


def find_cont_to_doc_type(doc_type, zaw_words):
    '''
    find contiunuation to doc type (words preparing for description of keywords like: 'zawierającej, 'mówiącej o')
    :param doc_type: dict - selected doc_type
    :param zaw_words: list[dict] - list of possible continuation
    :return: - dict - selected continuation
    '''
    cont_word = random.choice(zaw_words)

    if cont_word['dozwolone_po'][0] == "all":
        return cont_word

    if cont_word['dozwolone_po'][0] == "not":
        while doc_type['baza'] in cont_word['dozwolone_po']:
            cont_word = random.choice(zaw_words)
        return cont_word

    if cont_word['dozwolone_po'][0] == "only":
        if not doc_type['baza'] in cont_word['dozwolone_po']:
            cont_word = find_cont_to_doc_type(doc_type, zaw_words)
        return cont_word


def find_document_form(search_word:dict, doc_type:dict, count:str):
    '''

    :param search_word: dict - search word
    :param doc_type: dict - choosen document
    :param count: - form plural = "pl", single = "sg", (liczba osobowa)
    :return: word in right form, parameters for continuation
    '''
    doc_type_morph = morf.generate(doc_type['baza'])
    if search_word['nadpisz']:
        keys = list(search_word['nadpisz'].keys())
        if 'liczba' in keys:
            count = search_word['nadpisz']['liczba']

    if doc_type['odmiana']:
        for item in doc_type_morph:
            tags = item[2].split(':')
            if len(tags) > 3:
                if search_word['przypadek'] in tags[2].split('.') and tags[1] == count:
                    if item[4]:
                        if 'arch' not in ''.join(i for i in item[4]):
                            liczba = tags[1]
                            przypadek = tags[2]
                            rodzaj = tags[3]
                            item_type = item
                    else:
                        liczba = tags[1]
                        przypadek = tags[2]
                        rodzaj = tags[3]
                        item_type = item
    else:
        item_type = [doc_type['baza']]

    if doc_type['nadpisz']:
        keys = list(doc_type['nadpisz'].keys())
        if 'przypadek' in keys:
            przypadek = doc_type['nadpisz']['przypadek']
        if 'rodzaj' in keys:
            rodzaj = doc_type['nadpisz']['rodzaj']
        if 'liczba' in list(doc_type['nadpisz'].keys()):
            liczba = doc_type['nadpisz']['liczba']

    right_type_val = {'przypadek': przypadek.split('.'),
                      'liczba': liczba.split('.'),
                      'rodzaj': rodzaj.split('.')}

    return item_type, right_type_val


def find_verb_form(cont_word, right_type_val):
    '''

    :param cont_word: choosen continuation word
    :param right_type_val: parameters for continuation (from doc type)
    :return: rigth type cont word
    '''
    if cont_word['nadpisz']:
        keys = list(cont_word['nadpisz'].keys())
        if 'liczba' in keys:
            right_type_val['liczba'] = [cont_word['nadpisz']['liczba']]
        if 'przypadek' in keys:
            right_type_val['przypadek'] = [cont_word['nadpisz']['przypadek']]
        if 'rodzaj' in keys:
            right_type_val['rodzaj'] = [cont_word['nadpisz']['rodzaj']]

    # print(cont_word)
    if cont_word['odmiana']:
        b = morf.generate(cont_word['baza'])
        for item in b:
            tags = item[2].split(':')
            przyp = right_type_val['przypadek']
            if tags[0] == cont_word['fleksem']:
                if any(x in right_type_val['liczba'] for x in tags[1].split('.')):
                    if any(x in right_type_val['rodzaj'] for x in tags[3].split('.')):
                        if any(x in przyp for x in tags[2].split('.')) and tags[-1] != "neg":
                            czas = item[0]
    else:
        czas = cont_word['baza']

    if cont_word['potrzebny_przed']:
        czas = cont_word['potrzebny_przed'] + ' ' + czas

    return czas


def get_doc_num(i):
    '''
    get number of doc_types to ask for
    :param i: number of doc types
    :return:
    '''
    num_doc = 1
    if random.uniform(0, 1) > i:
        num_doc = 2
        if random.uniform(0, 1) > i:
            num_doc = 3
            if random.uniform(0, 1) > i:
                num_doc = 4
    return num_doc


def prepare_doc_selection(num_doc, search_word, document_types):
    '''
    select and prepare selected number of ducuments
    :param num_doc: number of documents to choose
    :param search_word: selected search word
    :param document_types: list of possible doc_types
    :return:
    '''
    selected_doctypes = []
    while len(selected_doctypes) < num_doc:
        doc = find_doc_to_search_word(search_word, document_types)
        if doc not in selected_doctypes:
            selected_doctypes.append(doc)

    if num_doc > 1:
        for i in range(len(selected_doctypes)):
            if selected_doctypes[i]['baza'] in ["coś", "czegoś"]:
                cos = selected_doctypes.pop(i)
                selected_doctypes.append(cos)
                break

    return selected_doctypes


def prepare_key_selection(num_keys, keywords):
    '''
    preapare key selection
    :param num_keys: number of keys to ask for
    :param keywords: list of keywords
    :return:
    '''
    selected_keywords = []
    while len(selected_keywords) < num_keys:
        key = random.choice(keywords)
        if key not in selected_keywords:
            selected_keywords.append(key)

    return selected_keywords

def get_keyword_form(key, cont_word):
    # get right keyword form
    keys = key.split(' ')
    keyw = keys[0]
    try:
        przypadek = cont_word['przypadek']
        aaa = morf.generate(keyw)
        for item in aaa:
            tags = item[2].split(':')
            if przypadek in tags[2].split('.'):
                if 'arch' not in ''.join(i for i in item[4]):
                    #print(item[0])
                    if len(keys) > 1:
                        czas = item[0]  +' '+' '.join(keys[1:])
                    else:
                        czas = item[0]
                    return czas
    except:
        czas = key
        return czas


def get_slots(keyword_sentence_part, choice_type):
    '''
    prepare slots for selected keyword or doc_type
    :param keyword_sentence_part:
    :param choice_type:
    :return:
    '''

    keyword_slots = []
    for i in range(len(keyword_sentence_part.split(' '))):
        if i == 0:
            keyword_slots.append('B-' + choice_type)
        else:
            keyword_slots.append('I-' + choice_type)

    return keyword_slots


def get_choice_slot(choice_word, choice_type):
    '''
    prepare slots for choice word
    :param choice_word:
    :param choice_type:
    :return:
    '''
    keyword_slots = []
    for i in range(len(choice_word.split(' '))):
        if i == 0:
            keyword_slots.append('B-Choice-' + choice_type)
        else:
            keyword_slots.append('I-Choice-' + choice_type)

    return keyword_slots


def get_l_operator(choice_words_and, choice_words_or, p1, p2):
    '''
    select choice word
    :param choice_words_and:
    :param choice_words_or:
    :param p1:
    :param p2:
    :return:
    '''
    rand_num = random.uniform(0, 1)
    if rand_num <= p1:
        a = random.choice(choice_words_and)
        slots = get_choice_slot(a, 'and')
        or_word = " " + a
    elif rand_num > p1 and rand_num < p2:
        a = random.choice(choice_words_or)
        slots = get_choice_slot(a, 'or')
        or_word = " " + a
    else:
        a = ","
        slots = ['O']
        or_word = a
    return or_word, slots, a


def prepare_key_sent(keyword_list, cont_word):
    '''
    prepare part of sentence describing keys
    :param keyword_list:
    :param cont_word:
    :return:
    '''
    keyword_sentence_part = []
    keyword_slots = []
    keyword_tokens = []
    # print(keyword_list)

    for key in keyword_list:
        czas = ''
        czas = get_keyword_form(key, cont_word)
        if type(czas) is list:
            czas = ' '.join(czas)
        if not czas:
            czas = key

        keyword_sentence_part.append(czas)
        # print(keyword_sentence_part)

    sentence = ''
    if len(keyword_sentence_part) > 1:

        choice_neutral = [","]
        choice_words_and = ["i", "oraz", "a także", "i do tego", "oraz jednocześnie"]
        choice_words_or = ["lub", "albo", "bądź", "ewentualnie", "lub też", "bądź też", "lub ewentualnie",
                           "albo ewentualnie"]

        for i in range(len(keyword_sentence_part) - 1):
            if i == 0:
                sentence += keyword_sentence_part[0]
                keyword_slots.extend(get_slots(keyword_sentence_part[0]))
                keyword_tokens.extend(keyword_sentence_part[0].split(' '))
            else:
                or_word, slots, a = get_l_operator(choice_words_and, choice_words_or, 0.2, 0.4)
                sentence += or_word + ' ' + keyword_sentence_part[i]
                keyword_slots.extend(slots + get_slots(keyword_sentence_part[i], 'keyword'))
                keyword_tokens.extend([word for word in a.split(' ')] + keyword_sentence_part[i].split(' '))

        or_word, slots, a = get_l_operator(choice_words_and, choice_words_or, 0.5, 0.9)

        sentence += or_word + ' ' + keyword_sentence_part[-1]
        keyword_slots.extend(slots + get_slots(keyword_sentence_part[-1], 'keyword'))
        keyword_tokens.extend([word for word in a.split(' ')] + keyword_sentence_part[-1].split(' '))
    else:
        sentence = keyword_sentence_part[0]
        keyword_slots.extend(get_slots(keyword_sentence_part[0]))
        keyword_tokens.extend(keyword_sentence_part[0].split(' '))

    # print(sentence)
    return sentence, keyword_slots, keyword_tokens


def prepare_doc_sent(item_types):
    sentence = ''
    sentence_slots = []
    sentence_tokens = []
    choice_words_or = ["lub", "albo", "bądź", "ewentualnie", ",", "lub też", "bądź też"]
    choice_words_and = ["i", "oraz"]

    if len(item_types) > 1:
        for i in range(len(item_types) - 1):
            if i == 0:
                sentence += item_types[i][0]
                sentence_tokens.append(item_types[i][0])
                sentence_slots.append('Doc_type')
            else:
                or_word, slots, a = get_l_operator(choice_words_and, choice_words_or, 0.2, 0.4)
                sentence += or_word + ' ' + item_types[i][0]
                sentence_slots.extend(slots + get_slots(keyword_sentence_part[i], 'keyword'))
                sentence_tokens.extend([word for word in a.split(' ')] + item_types[i][0])
                sentence_slots.extend(['O', 'Doc_type'])

        or_word, slots, a = get_l_operator(choice_words_and, choice_words_or, 0.2, 0.7)

        sentence = sentence + or_word + ' ' + item_types[-1][0]
        sentence_slots.extend([doc_choice_slot(or_word, 'or')] + ['Doc_type'])
        sentence_tokens.extend([word for word in a.split(' ')] + [item_types[-1][0]])

    else:
        sentence = item_types[0][0]
        sentence_tokens.append(item_types[0][0])
        sentence_slots.append('Doc_type')

    return sentence, sentence_slots, sentence_tokens

def get_sentence_full(count, search_words, document_types, zaw_words, con_syn, keyword_list):
    list_of_sentences = []
    for i in range(count):
        count = 'sg'
        if random.uniform(0, 1) > 0.5:
            count = 'pl'
        doc_num = get_doc_num(0.5)
        search_word = random.choice(search_words)
        # doc_type = find_doc_to_search_word(search_word, document_types)
        doc_type = prepare_doc_selection(doc_num, search_word, document_types)

        search_word_slot = ['O' for elem in search_word['baza'].split(' ')]
        search_word_tokens = [elem for elem in search_word['baza'].split(' ')]

        item_types = []
        for i in range(doc_num - 1):
            [item_t, _] = find_document_form(search_word, doc_type[i], count)
            item_types.append(item_t)

        item_t, right_type_val = find_document_form(search_word, doc_type[doc_num - 1], count)
        item_types.append(item_t)
        # print(item_types)

        doc_sentence_part, doc_sentence_slots, doc_sentence_tokens = prepare_doc_sent(item_types)

        cont_word = find_cont_to_doc_type(doc_type[-1], zaw_words)
        czas = find_verb_form(cont_word, right_type_val)

        senten = search_word['baza'] + ' ' + doc_sentence_part + ' ' + czas

        tokens = search_word_tokens + doc_sentence_tokens + czas.split(' ')
        slots = search_word_slot + doc_sentence_slots + ['O' for word in czas.split(' ')]

        stop = False
        while cont_word['możliwa_kontynuacja'] and not stop:
            if cont_word['potrzebna_kontynuacja']:
                cont = random.choice(cont_word['moz_kontynuacja'])
                # print(cont)
                cont_word = next((item for item in con_syn if item['baza'] == cont), None)
                senten = senten + ' ' + cont_word['baza']
                tokens.extend(cont_word['baza'].split(' '))
                slots.extend(['O' for i in cont_word['baza'].split(' ')])

            elif random.uniform(0, 1) > 0.5:
                cont = random.choice(cont_word['moz_kontynuacja'])
                # print(cont)
                cont_word = next((item for item in con_syn if item['baza'] == cont), None)
                senten = senten + ' ' + cont_word['baza']
                tokens.extend(cont_word['baza'].split(' '))
                slots.extend(['O' for i in cont_word['baza'].split(' ')])
            else:
                stop = True

        keys = prepare_key_selection(get_doc_num(0.5), keyword_list)

        key_sentence_part, key_sentence_slots, key_sentence_tokens = prepare_key_sent(keys, cont_word)

        sentence = senten + ' ' + key_sentence_part
        #print(sentence)
        tokens = tokens + key_sentence_tokens
        slots = slots + key_sentence_slots
        #print(slots)
        sentence_dict = {'sentence': sentence, 'tokens': tokens, 'slots': slots}
        list_of_sentences.append(sentence_dict)

    return list_of_sentences