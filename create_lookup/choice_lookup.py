import json
import spacy
if __name__ == '__main__':
    nlp = spacy.load('/models/Spacy_lg/')
    words = [('i', 'AND'),
             ('oraz', 'AND'),
             ('a', 'AMB'),
             ('także', 'AND'),
             ('również', 'AND'),
             ('do', 'AMB'),
             ('tego', 'AMB'),
             ('jednocześnie', 'AND'),
             ('oraz', 'AND'),
             ('tylko', 'AMB'),
             ('nie', 'NEG'),
             ('ale', 'AMB'),
             ('bez', 'NEG'),
             ('lub', 'OR'),
             ('albo', 'OR'),
             ('bądź', 'OR'),
             ('ewentualnie', 'OR'),
             ('też', 'AMB'),
             ('czy', 'OR')
]

    dict_list = []
    for item in words:
        ww = {
            'word': item[0],
            'logic': item[1],
            'vector': nlp(item[0])[0].vector.tolist()
        }
        dict_list.append(ww)

    with open("../data/functionalities/lookups/lookup_choice.json", 'w', encoding='utf-8-sig') as f:
        json.dump(dict_list, f)