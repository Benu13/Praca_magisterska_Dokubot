import os

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import Dokubot.Dialga as DD
import random
from collections import Counter

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://txqbllhz:iUCeaEJXQIV9DiFks2gjbTxClw5ssOpx@mouse.db.elephantsql.com/txqbllhz'
app.config['SECRET_KEY'] = 'SZA2211SCK78XD'
db = SQLAlchemy(app)
app.static_folder = 'static'

config = {
    'OOV_handler_type': 'mimic',
    'correct_misspell': True,
    'spacy_size': 'md',
    'misspell_cor_algorithm': 'lev',
    'spacy_from_path': True,
    'spacy_disable': ["attribute_ruler", "ner", 'tagger', 'parser', 'morphologizer'],
    'paths': {
        'slot_filler_path':  'models/slot_filer/mimic_ls10.h5',
        'slot_lookup_path': 'data/functionalities/lookups/slot_lookup_mimic4.json',
        'choice_lookup_path': 'data/functionalities/lookups/lookup_choice.json',
        'spacy_path': 'models/Spacy_md/',
        'mimic_path': 'models/mimic/mimic_smol/mimic_smol.h5',
        'char2tok_path': 'models/mimic/mimic_smol/char_tokenizer_mimic_smol.json',
        'misspell_lookup_path': 'data/functionalities/lookups/lookup_docs.json'
    }

}

Dialog = DD.Dialog(config)
stage = 'start'
current_essence = 0
UNI_questions = []
stop_flag = False
essence_num = 0
pref_doc_asked = False
uni_type = None
found_data = None
found_updated = None
frequent = None
all_keys = None
doc_ids = []
fdq = True
debug_s = False
debug_q = False

class Document(db.Model):
    __tablename__ = 'Document'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    authors = db.Column(db.String)
    source = db.Column(db.String)
    url = db.Column(db.String)
    doc_type = db.Column(db.String)
    keywords = db.relationship("Keyword", back_populates="document")


class Keyword(db.Model):
    __tablename__ = 'Keyword'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String)
    value = db.Column(db.Float)
    document_id = db.Column(db.Integer, db.ForeignKey("Document.id"))
    document = db.relationship("Document", back_populates="keywords")


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', **locals())


@app.route("/get")
def get_bot_response():
    global current_essence, essence_num, UNI_questions, pref_doc_asked, uni_type, fdq, stage, stop_flag, found_data, \
        found_updated, frequent, all_keys, doc_ids, debug_s, debug_q

    userText = request.args.get('msg')
    if userText == 'debug slots':
        debug_s = True
        return("Debugowanie slotów włączone - rozmowa zakończy się po wyświetleniu slotów")
    if userText == 'debug query':
        debug_q = True
        return ("Debugowanie query włączone - rozmowa zakończy się po wyświetleniu query")

    if userText == 'debug off':
        debug_s = False
        debug_q = False
        return("Debugowanie wyłączone musisz zrestartować!")

    if userText == 'restart':
        Dialog.reset()
        stage = 'start'
        current_essence = 0
        UNI_questions = []
        stop_flag = False
        essence_num = 0
        pref_doc_asked = False
        fdq = True
        uni_type = None
        found_data = None
        found_updated = None
        frequent = None
        all_keys = None
        doc_ids = []

        return jsonify([random.choice(DD.retry_responses), random.choice(DD.greet_reactions),
                        random.choice(DD.ask_for_doc)])
    else:
        stop_flag = False

    while not stop_flag:
        if userText == 'restart':
            return "Zatrzymano, jeśli wystąpił jakiś problem wpisz 'restart' by zacząć od nowa."

        if stage == 'start' and userText != 'restart':
            if Dialog.isgreet(userText):
                return jsonify([random.choice(DD.greet_reactions), random.choice(DD.ask_for_doc)])
            elif len(DD.text_cleaner(userText)) < 2:
                return jsonify(["╭( ๐_๐)╮", random.choice(DD.ask_for_doc)])
            else:
                sentence = Dialog.extract(DD.text_cleaner(userText))
                if debug_s:
                    stage = 'start'
                    return jsonify(["Tokeny: " + ' '.join([w.word for w in sentence.Tokens]) ,"Sloty:" + ' '.join(sentence.sentence_slots)])

                Dialog.essence_operators = sentence.essence_operators
                essence_num = len(sentence.essence) - 1
                for i in range(essence_num + 1):
                    Dialog.essence.append(sentence.essence[i])

                stage = 'check_validity'

        if stage == 'check_validity':
            dd = Dialog
            if Dialog.essence[current_essence]['doc_types']:
                if len(Dialog.essence[current_essence]['doc_types']) > 1:
                    if (len(Dialog.essence[current_essence]['doc_types']) !=
                            len(Dialog.essence[current_essence]['doc_operators']) + 1):
                        if current_essence == 0:
                            stage = 'start'
                            return jsonify(["Wybacz nie rozumiem polecenia!", "Chyba brakło ci spójnika między dwoma typami dokumentów."])
                        else:
                            stage = 'start'
                            return jsonify(["Wybacz nie rozumiem tej części polecenia!"])
            if Dialog.essence[current_essence]['keywords']:
                if len(Dialog.essence[current_essence]['keywords']) > 1:
                    if (len(Dialog.essence[current_essence]['keywords']) !=
                            len(Dialog.essence[current_essence]['key_operators']) + 1):
                        if current_essence == 0:
                            stage = 'start'
                            return jsonify(["Wybacz nie rozumiem polecenia!", "Chyba brakło ci spójnika między dwoma kluczami."])
                        else:
                            stage = 'start'
                            return jsonify(["Wybacz nie rozumiem tej części polecenia!"])

            if essence_num > 0 and current_essence <= essence_num-1:
                if not Dialog.essence[current_essence+1]['keywords']:
                    Dialog.essence[current_essence]['doc_types'].extend(Dialog.essence[current_essence+1]['doc_types'])
                    Dialog.essence[current_essence]['doc_operators'].append(Dialog.essence_operators[current_essence])
                    essence_num -= 1
                    Dialog.essence[current_essence+1].pop()

            stage = 'preprocess_doc'

        if stage == 'preprocess_doc':
            uni_type = 'docs'
            Dialog.doc_logic = ('CL', [])
            stage = 'preprocess_key'
            #if Dialog.doc_logic[0] != 'CL':
            #    Dialog.doc_logic = Dialog.LH.solve(Dialog.essence[current_essence]['doc_types'],
            #                                       Dialog.essence[current_essence]['doc_operators'])
            #    if Dialog.doc_logic[0] == 'UNI':
            #        UNI_questions = service_question_UNI(Dialog.doc_logic, Dialog.essence[current_essence], 'docs')
            #        stage = 'ask_solution_UNI'

            #    if Dialog.doc_logic[0] == 'NO':
            #        Dialog.doc_logic = ('CL', [])

            #    if Dialog.doc_logic[0] == 'SCL':
            #        stage = 'ask_solution_SCL'
            #else:
            #    Dialog.doc_logic_all.append(Dialog.doc_logic)
            #    stage = 'preprocess_key'

        if stage == 'preprocess_key':
            uni_type = 'keys'
            if Dialog.key_logic[0] != 'CL':

                Dialog.key_logic = Dialog.LH.solve(Dialog.essence[current_essence]['keywords'],
                                                   Dialog.essence[current_essence]['key_operators'])
                if Dialog.key_logic[0] == 'UNI':
                    UNI_questions = service_question_UNI(Dialog.key_logic, Dialog.essence[current_essence], 'keys')
                    stage = 'ask_solution_UNI'

                if Dialog.key_logic[0] == 'NO':
                    Dialog.key_logic = ('CL', [])

                if Dialog.key_logic[0] == 'SCL':
                    stage = 'ask_solution_SCL'
            else:
                Dialog.key_logic_all.append(Dialog.key_logic[1])
                stage = 'check_path'
                # return random.choice(DD.prep_ready)

        if stage == 'check_path':
            uni_type = None

            if not Dialog.doc_pref:
                Dialog.doc_all_pref(Dialog.essence[current_essence]['doc_types'])
            if not Dialog.doc_pref and not pref_doc_asked:
                stage = 'ask_pref_doc'
                return jsonify([random.choice(DD.ask_pref_doc), "wpisz jeden typ np. 'książka' lub całym zdaniem", "np. szukam książki lub dokumentu"])
            elif Dialog.doc_logic[1] and not Dialog.key_logic[1]:
                stage = 'ask_keys'
                return jsonify([random.choice(DD.ask_for_keys), "Wpisz całym zdaniem jak coś bo inaczej nie zrozumiem","np. może być coś o kotach"])
            else:
                stage = 'search_narrowing'

        # get data from db and start narrowing
        if stage == 'search_narrowing':
            if found_data is None:
                query, all_keys = Dialog.keys_to_query()

                if debug_q:
                    stage = 'start'
                    return("Query:" + query)

                query = db.text(query)

                req = db.session.query(Document).from_statement(query)

                found_data, count, frequent = Dialog.prep_query_data(req, all_keys)
                if found_data.empty:
                    return jsonify(["Niestety nie udało sie znaleźć żadnych dokumentów w tym temacie, wybacz.",
                                    "Jak to mawia pewien kowal:", "Zawiedliśmy.", "( ͡° ͜ʖ ~)",
                                    "Wpisz restart żeby zacząć od początku!"])

                found_updated = found_data.sort_values('score', ascending=False)

                if not Dialog.doc_all_flag:
                    if Dialog.doc_pref:
                        found_updated = found_data.loc[found_data['type'].isin(Dialog.doc_pref)]
                        count = len(found_updated)
                        if count < 1:
                            stage = 'search_pref_failed'
                            return jsonify(["Nie udało się znaleźć typu/ów: " + ', '.join(
                                [i for i in Dialog.doc_pref]) + " w zadanym temacie.",
                                            "Udało się jednak znaleźć inne typy dokumentów w zadanym temacie.",
                                            "Czy chcesz je uwzglednić? (tak/nie)"])
                        else:
                            found_updated = found_updated.sort_values('score', ascending=False).reset_index(drop=True)
                            frequent = Counter(get_keys_from_pd(found_updated, all_keys)).most_common()
                    else:
                        return "Coś poszło nie tak, wpisz 'restart' żeby zacząć od nowa :/"

                question = "Udało mi się znaleźć %i pasujących wyników, " % count

            else:
                if not found_data.empty:
                    found_updated = found_updated.sort_values('score', ascending=False)
                    found_updated = found_updated.reset_index(drop=True)
                    count = len(found_updated)

                    question = "No to mamy %i pasujących wyników, " % count
                else:
                    return jsonify(["Niestety nie udało sie znaleźć dokumentów o szukanym temacie ;_;",
                                    "Żeby spróbować od nowa wpisz 'restart'"])

            if count == 1:
                out = ["To wszystko, jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info'.",
                       "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                       "I jeszcze jedno - jeśli chcesz zacząć od nowa wpisz 'restart'",
                       "To wszystko z mojej strony (´^ω^)ノ."]
                out2 = ["Z tej części to tyle!",
                        "Jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info'.",
                        "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                        "A jeśli chcesz przejść od razu dalej to wpisz 'dalej'."]
                stage = 'after_list'
                question = "No to mamy tylko jeden wynik!"
                if current_essence < essence_num:
                    return jsonify([question, "1. " + found_updated.title.iloc[0] + "; Wskaźnik: " + str(
                        found_updated.score.iloc[0])] + out2)
                else:
                    return jsonify([question, "1. " + found_updated.title.iloc[0] + "; Wskaźnik: " + str(
                        found_updated.score.iloc[0])] + out)

            if count < 10:
                stage = 'list_results'
                question += "podesłać wszystkie czy tylko najlepszy?"
                return question

            elif count >= 10 and frequent[0][1] > 1:
                stage = 'search_results'
                question += 'co teraz robimy?'
                qq = [question, "1. Pokaż kilka najlepszych", "2. Dodaj tag", "3. Pomóż mi zawęzić wyszukiwanie",
                      "tutaj musisz wybrać numerek jak coś (˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。."]
                return jsonify(qq)

            else:
                stage = 'search_results'
                question += 'co teraz robimy?'
                qq = [question, "1. Pokaż kilka najlepszych", "2. Dodaj tag",
                      "tutaj musisz wybrać numerek jak coś (˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。."]
                return jsonify(qq)

        if stage == 'search_pref_failed':
            if userText.lower() == 'tak':
                Dialog.doc_all_flag = True
                found_updated = found_data
                stage = 'search_narrowing'
            elif userText.lower() == 'nie':
                stage = 'start'
                return 'Zawsze możesz spróbować ponownie ;_;'
            else:
                return 'Nie rozumiem, po prostu wpisz tak lub nie ( ง `ω´ )۶'

        if stage == 'search_results':
            try:
                choice_num = int(userText)
            except ValueError:
                return "Kolego, bo się pogniewamy"

            if choice_num == 1:
                stage = 'list_results'
                userText = 'wszystkie'
            elif choice_num == 2:
                stage = 'add_tag'
                return random.choice(DD.ask_tag)
            elif choice_num == 3 and frequent[0][1] > 1:
                stage = 'help_narrow_ask'
            else:
                return "Tylko że takiego wyboru nie ma..."

        if stage == 'add_tag':
            df_added_tag = filter_in_data(found_updated, userText.lower())
            if not df_added_tag.empty:
                found_updated = df_added_tag
                all_keys.append(userText.lower())
                frequent = Counter(get_keys_from_pd(found_updated, all_keys)).most_common()
                stage = 'search_narrowing'
            else:
                stage = 'tag_not_found'
                return jsonify(["Nie znalazłem wyniku zawierającego szukany przez Ciebie tag!",
                                'Wrócić do szukania?', 'tak/nie'])

        if stage == 'tag_not_found':
            if userText.lower() == 'tak':
                stage = 'search_narrowing'
            else:
                return jsonify(["Zawiedliśmy.", "Żeby zacząć od nowa wpisz 'restart'"])

        if stage == 'help_narrow_ask':
            if frequent:
                if frequent[0][1] > 1:
                    if frequent[0][1] != len(found_updated):
                        question = "Czy dokument którego szukasz powinien zawierać tag '%s' czy nie?" % frequent[0][0]
                        stage = 'help_narrow_answer'
                        return jsonify([question, "tak/nie/nie wiem/powrót"])
                    else:
                        userText = 'nie wiem'
                        stage = 'help_narrow_answer'
                else:
                    stage = 'search_narrowing'
            else:
                stage = 'search_narrowing'

        if stage == 'help_narrow_answer':
            if userText.lower() == 'tak':
                found_updated = filter_in_data(found_updated, frequent[0][0])
                # found_updated = found_updated.reset_index()
                all_keys.append(frequent[0][0])
                frequent = Counter(get_keys_from_pd(found_updated, all_keys)).most_common()
                stage = 'help_narrow_ask'
            elif userText.lower() == 'nie':
                found_updated = filter_not_in_data(found_updated, frequent[0][0])
                # found_updated = found_updated.reset_index()
                frequent = Counter(get_keys_from_pd(found_updated, all_keys)).most_common()
                stage = 'help_narrow_ask'
            elif userText.lower() == 'nie wiem':
                all_keys.append(frequent[0][0])
                frequent.pop(0)
                stage = 'help_narrow_ask'
            elif userText.lower() == 'powrót':
                stage = 'search_narrowing'
            else:
                return ('Nie ma takiego wyboru!')

        if stage == "after_list":
            ut = userText.lower().split(' ')
            if userText.lower() == 'dalej' and current_essence < essence_num:
                current_essence += 1
                stage = 'check_validity'
                found_data = None
                found_updated = None
                frequent = None
                all_keys = None
                doc_ids = []
                Dialog.soft_reset()

            elif userText.lower() == 'szukanie':
                found_data = None
                found_updated = None
                frequent = None
                all_keys = None
                doc_ids = []
                stage = 'search_narrowing'

            elif ut[0] == 'info':
                if len(ut) == 1:
                    rr = db.session.query(Document).get(int(found_updated.id.iloc[0]))
                    tags = []
                    for tag in rr.keywords:
                        tags.append(tag.key)
                    return jsonify(['Tytuł: ' + rr.title, "Autorzy: " + rr.authors, 'Typ dokumentu:' + rr.doc_type,
                                    'Tagi: ' + ', '.join(tags), "URL: " + rr.url])
                try:
                    if int(ut[1]) in range(1, len(doc_ids) + 1):
                        rr = db.session.query(Document).get(int(doc_ids[int(ut[1]) - 1]))
                        tags = []
                        for tag in rr.keywords:
                            tags.append(tag.key)

                        return jsonify(['Tytuł: ' + rr.title, "Autorzy: " + rr.authors, 'Typ dokumentu: ' + rr.doc_type,
                                        'Tagi: ' + ', '.join(tags), "URL: " + rr.url])
                    else:
                        return "Zły numerek!"
                except ValueError:
                    return "Zły numerek!"
            else:
                return "Wybacz, nie rozumiem ╥﹏╥"

        if stage == 'list_results':
            stage = "after_list"

            if userText.lower() in DD.select_best:
                answer = []
                doc_num = 1
                if Dialog.doc_pref and Dialog.doc_all_flag:
                    for preffered in Dialog.doc_pref:
                        best = found_updated[found_updated.type == preffered]
                        if not best.empty:
                            s = "Najlepszy dokument typu: %s" % preffered
                            answer.extend([s, str(doc_num) + ". " + best.title.iloc[0] + "; Wskaźnik: " + str(
                                best.score.iloc[0])])
                            doc_num += 1
                            doc_ids.append(best.id.iloc[0])
                        else:
                            s = "Nie udało się znaleźć preferowanego typu dokumentu: %s w znalezionych pozycjach." % preffered
                            answer.append(s)

                    if found_updated.type.iloc[0] not in Dialog.doc_pref:
                        s = "Najlepszy dokument spoza preferowanych typów: "
                        answer.extend([s, str(doc_num) + ". " + found_updated.title.iloc[0] + "; Wskaźnik: " + str(
                            found_updated.score.iloc[0])])
                        doc_ids.append(found_updated.id.iloc[0])
                else:
                    tt = "Najlepsza znaleziona pozycja jest dokumentem typu: %s" % found_updated.type.iloc[0]
                    answer = [tt, found_updated.title.iloc[0] + "; Wskaźnik: " + str(found_updated.score.iloc[0])]

                out = [
                    "To wszystko, jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info {numer_pozycji}'.",
                    "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                    "I jeszcze jedno - jeśli chcesz zacząć od nowa wpisz 'restart'",
                    "To wszystko z mojej strony (´^ω^)ノ."]

                out2 = ["Z tej części to tyle!",
                        "Jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info'.",
                        "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                        "A jeśli chcesz przejść od razu dalej to wpisz 'dalej'."]

                if current_essence < essence_num:
                    return jsonify(answer + out2)
                else:
                    return jsonify(answer + out)

            elif userText.lower() in DD.select_all:
                docs_found = []
                out = [
                    "To wszystko, jeśli potrzebujesz dodatkowych informacji o danej pozycji wpisz 'info {numer_pozycji}'.",
                    "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                    "I jeszcze jedno - jeśli chcesz zacząć od nowa wpisz 'restart'",
                    "To wszystko z mojej strony (´^ω^)ノ."]
                out2 = ["Z tej części to tyle!",
                        "Jeśli potrzebujesz dodatkowych informacji o danej pozycji wpisz 'info {numer_pozycji}.",
                        "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                        "A jeśli chcesz przejść od razu dalej to wpisz 'dalej'."]

                for i in range(min(len(found_updated), 10)):
                    stage = "after_list"
                    docs_found.append(str(i + 1) + ". " + found_updated.title.iloc[i] + "; Typ: " +
                                      found_updated.type.iloc[i] + "; Wskaźnik: " + str(found_updated.score.iloc[i]))
                    doc_ids.append(found_updated.id.iloc[i])

                if current_essence < essence_num:
                    return jsonify(docs_found + out2)
                else:
                    return jsonify(docs_found + out)

            else:
                return "Wybacz, nie zrozumiałem jeśli chcesz wszystkie wpisz 'wszystkie' jeśli najlepszy wpisz 'najlepszy'."

        # Getting additional information from user
        if stage == 'ask_pref_doc':
            pref_doc_asked = True
            if Dialog.isnegation(userText) and userText != 'restart':
                Dialog.doc_all_flag = True
                stage = 'check_path'
            else:
                if len(userText.split(' ')) > 1:
                    Pdoc = Dialog.extract(DD.text_cleaner(userText))
                    if Pdoc.essence[0]['doc_types']:
                        Dialog.doc_logic = ['None']
                        Dialog.essence[current_essence]['doc_types'] = Pdoc.essence[0]['doc_types']
                        Dialog.essence[current_essence]['doc_operators'] = Pdoc.essence[0]['doc_operators']
                        del Pdoc
                        stage = 'preprocess_doc'
                    else:
                        return (
                            "Wybacz nie zrozumiałem, wpisz typ dokumentu jako jedno słowo np. 'książka' lub całym zdaniem np. 'szukam książki lub dokumentu' (▀̿Ĺ̯▀̿ ̿)")
                else:
                    Dtyp = Dialog.check_simil(userText)
                    if Dtyp:
                        Dialog.doc_logic = ['None']
                        Dialog.essence[current_essence]['doc_types'] = [Dtyp]
                        Dialog.essence[current_essence]['doc_operators'] = []
                        # Dialog.doc_pref.append(Dtyp.origin)
                        stage = 'preprocess_doc'
                    else:
                        return (
                            "Wybacz nie zrozumiałem, wpisz typ dokumentu jako jedno słowo np. 'książka' lub całym zdaniem np. 'szukam książki lub dokumentu' (▀̿Ĺ̯▀̿ ̿)")

        if stage == 'ask_keys':
            if Dialog.isnegation(userText) and userText != 'restart':
                return jsonify([random.choice(DD.dead_end), 'Aby zacząć od nowa wpisz ''restart'' :P'])
            else:
                try:
                    Pkey = Dialog.extract(DD.text_cleaner(userText))
                    if Pkey.essence[0]['keywords']:
                        Dialog.key_logic = ['None']
                        Dialog.essence[current_essence]['keywords'] = Pkey.essence[0]['keywords']
                        Dialog.essence[current_essence]['key_operators'] = Pkey.essence[0]['key_operators']
                        stage = 'preprocess_key'
                        del Pkey
                    else:
                        return ('Coś poszło nie tak, niestety musisz zrestartować, następnym razem spróbuj pełnym zdaniem (▀̿Ĺ̯▀̿ ̿)')
                except:
                    return ('Coś poszło nie tak, niestety musisz zrestartować, następnym razem spróbuj pełnym zdaniem (▀̿Ĺ̯▀̿ ̿)')

        # preprocess stages
        if stage == 'ask_solution_UNI':
            question = [random.choice(DD.UNI_found), "(musisz wybrać numerek)"]
            for j in UNI_questions[0][2]:
                question.append(str(j[0]) + ". " + j[2])
            stage = 'answer_solution_UNI'
            return jsonify(question)

        if stage == 'ask_solution_SCL':
            stage = 'answer_solution_SCL'
            if uni_type == 'docs':
                return ask_solution_SCL(Dialog.doc_logic)
            elif uni_type == 'keys':
                return ask_solution_SCL(Dialog.key_logic)

        if stage == 'answer_solution_UNI':
            solved, solution = service_solution_UNI(UNI_questions[0], Dialog.essence[current_essence], uni_type,
                                                    userText)
            if not solved:
                return jsonify(solution)
            else:
                Dialog.essence[current_essence] = solution
                UNI_questions.pop(0)
                if UNI_questions:
                    stage = 'ask_solution_UNI'
                else:
                    if uni_type == 'docs':
                        stage = 'preprocess_doc'
                    if uni_type == 'keys':
                        stage = 'preprocess_key'

        if stage == 'answer_solution_SCL':
            if uni_type == 'docs':
                solved, solution = service_solution_SCL(Dialog.doc_logic, userText)
                if not solved:
                    return solution
                else:
                    Dialog.doc_logic = solution
                    stage = 'preprocess_doc'

            elif uni_type == 'keys':
                solved, solution = service_solution_SCL(Dialog.key_logic, userText)
                if not solved:
                    return solution
                else:
                    Dialog.key_logic = solution
                    stage = 'preprocess_key'


###
def ask_solution_SCL(logic):
    question = [random.choice(DD.SCL_found)]
    for i in range(len(logic[1])):
        question.append((str(i + 1) + '. ' + logic[1][i][0]))

    return jsonify(question)


####
def service_question_UNI(logic, essence, op_type):
    if op_type == 'docs':
        keys = 'doc_types'
        operators = 'doc_operators'
    if op_type == 'keys':
        keys = 'keywords'
        operators = 'key_operators'

    choices = []
    for i in logic[1]:
        # serve uni token/s
        choice = []
        num = 1
        for l in essence[operators][i].tokens:
            if l.logic != 'AMB':
                choice.append((num, l.logic, ' '.join(
                    [essence[keys][i].word, l.word, essence[keys][i + 1].word])))
                num += 1

        choices.append((i, num, choice))

    return choices


def service_solution_UNI(choice, essence, op_type, user_choice):
    if op_type == 'docs':
        operators = 'doc_operators'
    if op_type == 'keys':
        operators = 'key_operators'

    try:
        uc_int = int(user_choice)
        if uc_int not in range(1, choice[1]):
            return False, [random.choice(DD.wrong_choice), "Po prostu wybierz numerek"]
        else:
            essence[operators][choice[0]].logic = choice[2][uc_int - 1][1]
            if choice[2][uc_int - 1][1] == 'OR':
                essence[operators][choice[0]].logic_pl = 'lub'
            if choice[2][uc_int - 1][1] == 'AND':
                essence[operators][choice[0]].logic_pl = 'i'
    except ValueError:
        return False, "Opanuj się, tutaj masz tylko wybrać numerek"

    return True, essence


def service_solution_SCL(logic, user_choice):
    try:
        uc_int = int(user_choice)
        if uc_int not in range(1, len(logic[1]) + 1):
            return False, random.choice(DD.wrong_choice)
        else:
            logic = ('CL', logic[1][uc_int - 1][1])
    except ValueError:
        return False, "Opanuj się, tutaj masz tylko wybrać numerek"

    return True, logic


def get_keys_from_pd(pd, all_keys):
    all_key = []
    for i, row in pd.iterrows():
        all_key += [x for x in row.keywords if x not in all_keys]

    return all_key


def filter_in_data(df, key):
    mask = df.keywords.apply(lambda x: key in x)
    df2 = df[mask]
    for ind, row in df2.iterrows():
        df2['score'][ind] += row['keywords_scores'][row['keywords'].index(key)]
    return df2


def filter_not_in_data(df, key):
    mask = df.keywords.apply(lambda x: key not in x)
    df2 = df[mask]
    return df2


if __name__ == '__main__':
    port = os.environ.get("PORT", 5000)
    app.run(debug=False, host="0.0.0.0", port=port)
