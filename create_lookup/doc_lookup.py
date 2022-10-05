import json
import spacy
if __name__ == '__main__':
    nlp = spacy.load('/models/Spacy_lg/')
    words = [('coś', 'sg', 'coś'),
             ('czegoś', 'sg', 'czegoś'),
             ('pozycja', 'sg', 'pozycja'),
             ('cokolwiek', 'sg', 'cokolwiek'),

             ('dokument', 'sg', 'dokument'),  ('naukowy', 'sg', 'naukowy'),   ('literacki', 'sg', 'literacki'),
             ('dokumentu', 'sg', 'dokument'), ('naukowego', 'sg', 'naukowy'), ('literackiego', 'sg', 'literacki'),
             ('dokumentów', 'pl', 'dokument'),('naukowych', 'pl', 'naukowy'), ('literackich', 'pl', 'literacki'),
             ('dokumenty', 'pl', 'dokument'), ('naukowe', 'pl', 'naukowy'),   ('literackie', 'pl', 'literacki'),

             ('książka', 'sg', 'książka'),
             ('książkę', 'sg', 'książka'),
             ('książki', 'hom', 'książka'),
             ('książek', 'pl', 'książka'),

             ('artykuł', 'sg', 'artykuł'),
             ('artykułu', 'sg', 'artykuł'),
             ('artykuły', 'pl', 'artykuł'),
             ('artykułów', 'pl', 'artykuł'),

             ('praca', 'sg', 'praca'), ('magisterska', 'sg', 'magisterska'),   ('inżynierska', 'sg', 'inżynierska'),   ('doktorancka', 'sg', 'doktorancka'),
             ('pracy', 'sg', 'praca'), ('magisterskiej', 'sg', 'magisterska'), ('inżynierskiej', 'sg', 'inżynierska'), ('doktoranckiej', 'sg', 'doktorancka'),
             ('pracę', 'sg', 'praca'), ('magisterską', 'sg', 'magisterska'),   ('inżynierską', 'sg', 'inżynierska'),   ('doktorancką', 'sg', 'doktorancka'),
             ('prace', 'pl', 'praca'), ('magisterskie', 'pl', 'magisterska'),  ('inżynierskie', 'pl', 'inżynierska'),  ('doktoranckie', 'pl', 'doktorancka'),
             ('prac', 'pl', 'praca'),  ('magisterskich', 'pl', 'magisterska'), ('inżynierskich', 'pl', 'inżynierska'), ('doktoranckich', 'pl', 'doktorancka'),

             ('rozprawa', 'sg', 'rozprawa'),
             ('rozprawę', 'sg', 'rozprawa'),
             ('rozprawy', 'hom', 'rozprawa'),
             ('rozpraw', 'pl', 'rozprawa'),

             ('recenzja', 'sg', 'recenzja'),
             ('recenzję', 'sg', 'recenzja'),
             ('recenzji', 'hom', 'recenzja'),
             ('recenzje', 'pl', 'recenzja'),

             ('esej', 'sg', 'esej'),  ('publicystyczny', 'sg', 'publicystyczny'),
             ('eseju', 'sg', 'esej'), ('publicystycznego', 'sg', 'publicystyczny'),
             ('eseji', 'pl', 'esej'), ('publicystycznych', 'pl', 'publicystyczny'),
             ('esejów', 'pl', 'esej'),

             ('patent', 'sg','patent'),
             ('patentu', 'sg','patent'),
             ('patenty', 'pl','patent'),
             ('patentów', 'pl','patent'),

             ('norma', 'sg', 'norma'),
             ('normę', 'sg', 'norma'),
             ('normy', 'hom', 'norma'),
             ('norm', 'pl', 'norma'),

             ('skrypt', 'sg', 'skrypt'),
             ('skryptu', 'sg', 'skrypt'),
             ('skrypty', 'pl', 'skrypt'),
             ('skryptów', 'pl', 'skrypt'),

             ('publikacja', 'sg', 'publikacja'),
             ('publikację', 'sg','publikacja'),
             ('publikacji', 'hom','publikacja'),
             ('publikacje', 'sg','publikacja'),

             ('podręcznik', 'sg', 'podręcznik'),
             ('podręcznika', 'sg', 'podręcznik'),
             ('podręczniki', 'pl', 'podręcznik'),
             ('podręczników', 'pl', 'podręcznik'),

             ('encyklopedia', 'sg', 'encyklopedia'),
             ('encyklopedii', 'hom','encyklopedia'),
             ('encyklopedie', 'pl','encyklopedia')]

    dict_list = []
    for item in words:
        ww = {
            'word': item[0],
            'form': item[1],
            'original': item[2],
            'vector': nlp(item[0])[0].vector.tolist()
        }
        dict_list.append(ww)

    with open("../data/functionalities/lookups/lookup_docs.json", 'w', encoding='utf-8-sig') as f:
        json.dump(dict_list, f)