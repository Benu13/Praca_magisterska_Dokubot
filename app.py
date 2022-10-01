import os

from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import Dokubot.Dialga as DD
import random
from collections import Counter

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://txqbllhz:iUCeaEJXQIV9DiFks2gjbTxClw5ssOpx@mouse.db.elephantsql.com/txqbllhz'
app.config['SECRET_KEY'] = 'SZA2211SCK78XD'
db = SQLAlchemy(app)
app.static_folder = 'static'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

config = {
    'OOV_handler_type': 'mimic',
    'correct_misspell': True,
    'spacy_size': 'md',
    'misspell_cor_algorithm': 'lev',
    'spacy_from_path': True,
    'spacy_disable': ["attribute_ruler", "ner", 'tagger', 'parser', 'morphologizer'],
    'paths': {
        'slot_filler_path':  'Models_deploy/mimic_ls11.h5',
        'slot_lookup_path': 'Models_deploy/slot_lookup_mimic4.json',
        'choice_lookup_path': 'Models_deploy/lookup_choice.json',
        'spacy_path': 'Models_deploy/Spacy_md/',
        'mimic_path': 'Models_deploy/mimic_super_smol.h5',
        'char2tok_path': 'Models_deploy/char_tok_small.json',
        'misspell_lookup_path': 'Models_deploy/lookup_docs.json'
    }

}

Dialog = DD.Dialog(config)

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
    # dialog variables
    session["stage"] = 'start'
    session["current_essence"] = 0
    session["UNI_questions"] = []
    session["stop_flag"] = False
    session["essence_num"] = 0
    session["pref_doc_asked"] = False
    session["uni_type"] = None
    session["found_data"] = None
    session["found_updated"] = None
    session["frequent"] = None
    session["all_keys"] = None
    session["doc_ids"] = []
    session["fdq"] = True
    session["debug_s"] = False
    session["debug_q"] = False
    
    # search variables
    session["doc_all_flag"] = False
    session["essence"] = []
    session["essence_operators"] = []
    session["doc_pref"] = []
    session["doc_logic"] = ['None']
    session["key_logic"] = ['None']
    session["key_logic_all"] = []

    return render_template('index.html', **locals())


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    if userText == 'debug slots':
        session["debug_s"] = True
        return("Debugowanie slotów włączone - rozmowa zakończy się po wyświetleniu slotów")
    if userText == 'debug query':
        session["debug_q"] = True
        return ("Debugowanie query włączone - rozmowa zakończy się po wyświetleniu query")

    if userText == 'debug off':
        session["debug_s"] = False
        session["debug_q"] = False
        return("Debugowanie wyłączone musisz zrestartować!")

    if userText == 'restart':
        session["stage"] = 'start'
        session["current_essence"] = 0
        session["UNI_questions"] = []
        session["stop_flag"] = False
        session["essence_num"] = 0
        session["pref_doc_asked"] = False
        session["fdq"] = True
        session["uni_type"] = None
        session["found_data"] = None
        session["found_updated"] = None
        session["frequent"] = None
        session["all_keys"] = None
        session["doc_ids"] = []
        session["doc_all_flag"] = False
        session["essence"] = []
        session["essence_operators"] = []
        session["doc_pref"] = []
        session["doc_logic"] = ['None']
        session["key_logic"] = ['None']
        session["key_logic_all"] = []

        return jsonify([random.choice(DD.retry_responses), random.choice(DD.greet_reactions),
                        random.choice(DD.ask_for_doc)])
    else:
        session["stop_flag"] = False

    while not session["stop_flag"]:
        if userText == 'restart':
            return "Zatrzymano, jeśli wystąpił jakiś problem wpisz 'restart' by zacząć od nowa."

        if session["stage"] == 'start' and userText != 'restart':
            if Dialog.isgreet(userText):
                return jsonify([random.choice(DD.greet_reactions), random.choice(DD.ask_for_doc)])
            elif len(DD.text_cleaner(userText)) < 2:
                return jsonify(["╭( ๐_๐)╮", random.choice(DD.ask_for_doc)])
            else:
                sentence = Dialog.extract(DD.text_cleaner(userText))
                if session["debug_s"]:
                    session["stage"] = 'start'
                    return jsonify(["Tokeny: " + ' '.join([w.word for w in sentence.Tokens]) ,"Sloty:" + ' '.join(sentence.sentence_slots)])

                session["essence_operators"] = sentence.essence_operators
                session["essence_num"] = len(sentence.essence) - 1
                for i in range(session["essence_num"] + 1):
                    session["essence"] .append(sentence.essence[i])

                session["stage"] = 'check_validity'

        if session["stage"] == 'check_validity':
            dd = Dialog
            if session["essence"][session["current_essence"]]['doc_types']:
                if len(session["essence"][session["current_essence"]]['doc_types']) > 1:
                    if (len(session["essence"][session["current_essence"]]['doc_types']) !=
                            len(session["essence"][session["current_essence"]]['doc_operators']) + 1):
                        if session["current_essence"] == 0:
                            session["stage"] = 'start'
                            return jsonify(["Wybacz nie rozumiem polecenia!", "Chyba brakło ci spójnika między dwoma typami dokumentów."])
                        else:
                            session["stage"] = 'start'
                            return jsonify(["Wybacz nie rozumiem tej części polecenia!"])
            if session["essence"][session["current_essence"]]['keywords']:
                if len(session["essence"][session["current_essence"]]['keywords']) > 1:
                    if (len(session["essence"][session["current_essence"]]['keywords']) !=
                            len(session["essence"][session["current_essence"]]['key_operators']) + 1):
                        if session["current_essence"] == 0:
                            session["stage"] = 'start'
                            return jsonify(["Wybacz nie rozumiem polecenia!", "Chyba brakło ci spójnika między dwoma kluczami."])
                        else:
                            session["stage"] = 'start'
                            return jsonify(["Wybacz nie rozumiem tej części polecenia!"])

            if session["essence_num"] > 0 and session["current_essence"] <= session["essence_num"]-1:
                if not session["essence"][session["current_essence"]+1]['keywords']:
                    session["essence"][session["current_essence"]]['doc_types'].extend(session["essence"][session["current_essence"]+1]['doc_types'])
                    session["essence"][session["current_essence"]]['doc_operators'].append( session["essence_operators"][session["current_essence"]])
                    session["essence_num"] -= 1
                    ssss = session["current_essence"]+1
                    session["essence"].pop(session["current_essence"]+1)

            session["stage"] = 'preprocess_doc'

        if session["stage"] == 'preprocess_doc':
            session["uni_type"] = 'docs'
            Dialog.doc_logic = ('CL', [])
            session["stage"] = 'preprocess_key'
            #if Dialog.doc_logic[0] != 'CL':
            #    Dialog.doc_logic = Dialog.LH.solve(session["essence"][session["current_essence"]]['doc_types'],
            #                                       session["essence"][session["current_essence"]]['doc_operators'])
            #    if Dialog.doc_logic[0] == 'UNI':
            #        session["UNI_questions"] = service_question_UNI(Dialog.doc_logic, session["essence"][session["current_essence"]], 'docs')
            #        session["stage"] = 'ask_solution_UNI'

            #    if Dialog.doc_logic[0] == 'NO':
            #        Dialog.doc_logic = ('CL', [])

            #    if Dialog.doc_logic[0] == 'SCL':
            #        session["stage"] = 'ask_solution_SCL'
            #else:
            #    Dialog.doc_logic_all.append(Dialog.doc_logic)
            #    session["stage"] = 'preprocess_key'

        if session["stage"] == 'preprocess_key':
            session["uni_type"] = 'keys'
            if session["key_logic"][0] != 'CL':

                session["key_logic"] = Dialog.LH.solve(session["essence"][session["current_essence"]]['keywords'],
                                                   session["essence"][session["current_essence"]]['key_operators'])
                if session["key_logic"][0] == 'UNI':
                    session["UNI_questions"] = service_question_UNI(session["key_logic"], session["essence"][session["current_essence"]], 'keys')
                    session["stage"] = 'ask_solution_UNI'

                if session["key_logic"][0] == 'NO':
                    session["key_logic"] = ('CL', [])

                if session["key_logic"][0] == 'SCL':
                    session["stage"] = 'ask_solution_SCL'
            else:
                session["key_logic_all"].append(session["key_logic"][1])
                session["stage"] = 'check_path'
                # return random.choice(DD.prep_ready)

        if session["stage"] == 'check_path':
            session["uni_type"] = None

            if not session["doc_pref"]:
                session["doc_pref"], session["doc_all_flag"] = Dialog.doc_all_pref(
                    session["essence"][session["current_essence"]]['doc_types'], session["doc_all_flag"])

            if not session["doc_pref"] and not session["pref_doc_asked"]:
                session["stage"] = 'ask_pref_doc'
                session["doc_all_flag"] = True
                return jsonify([random.choice(DD.ask_pref_doc), "wpisz jeden typ np. 'książka' lub całym zdaniem", "np. szukam książki lub artykułu"])
            elif Dialog.doc_logic[1] and not session["key_logic"][1]:
                session["stage"] = 'ask_keys'
                return jsonify([random.choice(DD.ask_for_keys), "Wpisz całym zdaniem jak coś bo inaczej nie zrozumiem","np. może być coś o kotach"])
            else:
                session["stage"] = 'search_narrowing'

        # get data from db and start narrowing
        if session["stage"] == 'search_narrowing':
            if session["found_data"] is None:
                query, session["all_keys"] = Dialog.keys_to_query(session["key_logic"])

                if session["debug_q"]:
                    session["stage"] = 'start'
                    return("Query:" + query)

                query = db.text(query)

                req = db.session.query(Document).from_statement(query)

                session["found_data"], count, session["frequent"] = Dialog.prep_query_data(req, session["all_keys"])
                if session["found_data"].empty:
                    return jsonify(["Niestety nie udało sie znaleźć żadnych dokumentów w tym temacie, wybacz.",
                                    "Jak to mawia pewien kowal:", "Zawiedliśmy.", "( ͡° ͜ʖ ~)",
                                    "Wpisz restart żeby zacząć od początku!"])

                session["found_updated"] = session["found_data"].sort_values('score', ascending=False)

                if not session["doc_all_flag"]:
                    if session["doc_pref"]:
                        session["found_updated"] = session["found_data"].loc[session["found_data"]['type'].isin(session["doc_pref"])]
                        count = len(session["found_updated"])
                        if count < 1:
                            session["stage"] = 'search_pref_failed'
                            return jsonify(["Nie udało się znaleźć typu/ów: " + ', '.join(
                                [i for i in session["doc_pref"]]) + " w zadanym temacie.",
                                            "Udało się jednak znaleźć inne typy dokumentów w zadanym temacie.",
                                            "Czy chcesz je uwzglednić? (tak/nie)"])
                        else:
                            session["found_updated"] = session["found_updated"].sort_values('score', ascending=False).reset_index(drop=True)
                            session["frequent"] = Counter(get_keys_from_pd(session["found_updated"], session["all_keys"])).most_common()
                    else:
                        return "Coś poszło nie tak, wpisz 'restart' żeby zacząć od nowa :/"

                question = "Udało mi się znaleźć %i pasujących wyników, " % count

            else:
                if not session["found_data"].empty:
                    session["found_updated"] = session["found_updated"].sort_values('score', ascending=False)
                    session["found_updated"] = session["found_updated"].reset_index(drop=True)
                    count = len(session["found_updated"])

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
                session["stage"] = 'after_list'
                question = "No to mamy tylko jeden wynik!"
                if session["current_essence"] < session["essence_num"]:
                    return jsonify([question, "1. " + session["found_updated"].title.iloc[0] + "; Wskaźnik: " + str(
                        session["found_updated"].score.iloc[0])] + out2)
                else:
                    return jsonify([question, "1. " + session["found_updated"].title.iloc[0] + "; Wskaźnik: " + str(
                        session["found_updated"].score.iloc[0])] + out)

            if count < 10:
                session["stage"] = 'list_results'
                question += "podesłać wszystkie czy tylko najlepszy?"
                return question

            elif count >= 10 and session["frequent"][0][1] > 1:
                session["stage"] = 'search_results'
                question += 'co teraz robimy?'
                qq = [question, "1. Pokaż kilka najlepszych", "2. Dodaj tag", "3. Pomóż mi zawęzić wyszukiwanie",
                      "tutaj musisz wybrać numerek jak coś (˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。."]
                return jsonify(qq)

            else:
                session["stage"] = 'search_results'
                question += 'co teraz robimy?'
                qq = [question, "1. Pokaż kilka najlepszych", "2. Dodaj tag",
                      "tutaj musisz wybrać numerek jak coś (˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。."]
                return jsonify(qq)

        if session["stage"] == 'search_pref_failed':
            if userText.lower() == 'tak':
                session["doc_all_flag"] = True
                session["found_updated"] = session["found_data"]
                session["stage"] = 'search_narrowing'
            elif userText.lower() == 'nie':
                session["stage"] = 'start'
                return 'Zawsze możesz spróbować ponownie ;_;'
            else:
                return 'Nie rozumiem, po prostu wpisz tak lub nie ( ง `ω´ )۶'

        if session["stage"] == 'search_results':
            try:
                choice_num = int(userText)
            except ValueError:
                return "Kolego, bo się pogniewamy"

            if choice_num == 1:
                session["stage"] = 'list_results'
                userText = 'wszystkie'
            elif choice_num == 2:
                session["stage"] = 'add_tag'
                return random.choice(DD.ask_tag)
            elif choice_num == 3 and session["frequent"][0][1] > 1:
                session["stage"] = 'help_narrow_ask'
            else:
                return "Tylko że takiego wyboru nie ma..."

        if session["stage"] == 'add_tag':
            df_added_tag = filter_in_data(session["found_updated"], userText.lower())
            if not df_added_tag.empty:
                session["found_updated"] = df_added_tag
                session["all_keys"].append(userText.lower())
                session["frequent"] = Counter(get_keys_from_pd(session["found_updated"], session["all_keys"])).most_common()
                session["stage"] = 'search_narrowing'
            else:
                session["stage"] = 'tag_not_found'
                return jsonify(["Nie znalazłem wyniku zawierającego szukany przez Ciebie tag!",
                                'Wrócić do szukania?', 'tak/nie'])

        if session["stage"] == 'tag_not_found':
            if userText.lower() == 'tak':
                session["stage"] = 'search_narrowing'
            else:
                return jsonify(["Zawiedliśmy.", "Żeby zacząć od nowa wpisz 'restart'"])

        if session["stage"] == 'help_narrow_ask':
            if session["frequent"]:
                if session["frequent"][0][1] > 1:
                    if session["frequent"][0][1] != len(session["found_updated"]):
                        question = "Czy dokument którego szukasz powinien zawierać tag '%s' czy nie?" % session["frequent"][0][0]
                        session["stage"] = 'help_narrow_answer'
                        return jsonify([question, "tak/nie/nie wiem/powrót"])
                    else:
                        userText = 'nie wiem'
                        session["stage"] = 'help_narrow_answer'
                else:
                    session["stage"] = 'search_narrowing'
            else:
                session["stage"] = 'search_narrowing'

        if session["stage"] == 'help_narrow_answer':
            if userText.lower() == 'tak':
                session["found_updated"] = filter_in_data(session["found_updated"], session["frequent"][0][0])
                # session["found_updated"] = session["found_updated"].reset_index()
                session["all_keys"].append(session["frequent"][0][0])
                session["frequent"] = Counter(get_keys_from_pd(session["found_updated"], session["all_keys"])).most_common()
                session["stage"] = 'help_narrow_ask'
            elif userText.lower() == 'nie':
                session["found_updated"] = filter_not_in_data(session["found_updated"], session["frequent"][0][0])
                # session["found_updated"] = session["found_updated"].reset_index()
                session["frequent"] = Counter(get_keys_from_pd(session["found_updated"], session["all_keys"])).most_common()
                session["stage"] = 'help_narrow_ask'
            elif userText.lower() == 'nie wiem':
                session["all_keys"].append(session["frequent"][0][0])
                session["frequent"].pop(0)
                session["stage"] = 'help_narrow_ask'
            elif userText.lower() == 'powrót':
                session["stage"] = 'search_narrowing'
            else:
                return ('Nie ma takiego wyboru!')

        if session["stage"] == "after_list":
            ut = userText.lower().split(' ')
            if userText.lower() == 'dalej' and session["current_essence"] < session["essence_num"]:
                session["current_essence"] += 1
                session["stage"] = 'check_validity'
                session["found_data"] = None
                session["found_updated"] = None
                session["frequent"] = None
                session["all_keys"] = None
                session["doc_ids"] = []
                Dialog.soft_reset()
                # search variables

                session["doc_all_flag"] = False
                session["doc_pref"] = []
                session["doc_logic"] = []
                session["key_logic"] = []
                session["key_logic_all"] = []

            elif userText.lower() == 'szukanie':
                session["found_data"] = None
                session["found_updated"] = None
                session["frequent"] = None
                session["all_keys"] = None
                session["doc_ids"] = []
                session["stage"] = 'search_narrowing'

            elif ut[0] == 'info':
                if len(ut) == 1:
                    rr = db.session.query(Document).get(int(session["found_updated"].id.iloc[0]))
                    tags = []
                    for tag in rr.keywords:
                        tags.append(tag.key)
                    return jsonify(['Tytuł: ' + rr.title, "Autorzy: " + rr.authors, 'Typ dokumentu:' + rr.doc_type,
                                    'Tagi: ' + ', '.join(tags), "URL: " + rr.url])
                try:
                    if int(ut[1]) in range(1, len(session["doc_ids"]) + 1):
                        rr = db.session.query(Document).get(int(session["doc_ids"][int(ut[1]) - 1]))
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

        if session["stage"] == 'list_results':
            session["stage"] = "after_list"

            if userText.lower() in DD.select_best:
                answer = []
                doc_num = 1
                if session["doc_pref"] and session["doc_all_flag"]:
                    for preffered in session["doc_pref"]:
                        best = session["found_updated"][session["found_updated"].type == preffered]
                        if not best.empty:
                            s = "Najlepszy dokument typu: %s" % preffered
                            answer.extend([s, str(doc_num) + ". " + best.title.iloc[0] + "; Wskaźnik: " + str(
                                best.score.iloc[0])])
                            doc_num += 1
                            session["doc_ids"].append(best.id.iloc[0])
                        else:
                            s = "Nie udało się znaleźć preferowanego typu dokumentu: %s w znalezionych pozycjach." % preffered
                            answer.append(s)

                    if session["found_updated"].type.iloc[0] not in session["doc_pref"]:
                        s = "Najlepszy dokument spoza preferowanych typów: "
                        answer.extend([s, str(doc_num) + ". " + session["found_updated"].title.iloc[0] + "; Wskaźnik: " + str(
                            session["found_updated"].score.iloc[0])])
                        session["doc_ids"].append(session["found_updated"].id.iloc[0])
                else:
                    tt = "Najlepsza znaleziona pozycja jest dokumentem typu: %s" % session["found_updated"].type.iloc[0]
                    answer = [tt, session["found_updated"].title.iloc[0] + "; Wskaźnik: " + str(session["found_updated"].score.iloc[0])]

                out = [
                    "To wszystko, jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info {numer_pozycji}'.",
                    "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                    "I jeszcze jedno - jeśli chcesz zacząć od nowa wpisz 'restart'",
                    "To wszystko z mojej strony (´^ω^)ノ."]

                out2 = ["Z tej części to tyle!",
                        "Jeśli potrzebujesz dodatkowych informacji o tej pozycji wpisz 'info'.",
                        "Jeśli chcesz rozpocząć od momentu pierwszego wyszukiwania wpisz 'szukanie'.",
                        "A jeśli chcesz przejść od razu dalej to wpisz 'dalej'."]

                if session["current_essence"] < session["essence_num"]:
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

                for i in range(min(len(session["found_updated"]), 10)):
                    session["stage"] = "after_list"
                    docs_found.append(str(i + 1) + ". " + session["found_updated"].title.iloc[i] + "; Typ: "
                                      + session["found_updated"].type.iloc[i] + "; Wskaźnik: "
                                      + str(session["found_updated"].score.iloc[i]))

                    session["doc_ids"].append(session["found_updated"].id.iloc[i])

                if session["current_essence"] < session["essence_num"]:
                    return jsonify(docs_found + out2)
                else:
                    return jsonify(docs_found + out)

            else:
                session["stage"] = "list_results"
                return "Wybacz, nie zrozumiałem jeśli chcesz wszystkie wpisz 'wszystkie' " \
                       "jeśli najlepszy wpisz 'najlepszy'."

        # Getting additional information from user
        if session["stage"] == 'ask_pref_doc':
            session["pref_doc_asked"] = True
            if Dialog.isnegation(userText) and userText != 'restart':
                session["doc_all_flag"] = True
                session["stage"] = 'check_path'
            else:
                if len(userText.split(' ')) > 1:
                    Pdoc = Dialog.extract(DD.text_cleaner(userText))
                    if Pdoc.essence[0]['doc_types']:
                        Dialog.doc_logic = ['None']
                        session["essence"][session["current_essence"]]['doc_types'] = Pdoc.essence[0]['doc_types']
                        session["essence"][session["current_essence"]]['doc_operators'] = Pdoc.essence[0]['doc_operators']
                        del Pdoc
                        session["stage"] = 'preprocess_doc'
                    else:
                        return (
                            "Wybacz nie zrozumiałem, wpisz typ dokumentu jako jedno słowo np. 'książka' lub całym "
                            "zdaniem np. 'szukam książki lub dokumentu' (▀̿Ĺ̯▀̿ ̿)")
                else:
                    Dtyp = Dialog.check_simil(userText)
                    if Dtyp:
                        Dialog.doc_logic = ['None']
                        session["essence"][session["current_essence"]]['doc_types'] = [Dtyp]
                        session["essence"][session["current_essence"]]['doc_operators'] = []
                        # session["doc_pref"].append(Dtyp.origin)
                        session["stage"] = 'preprocess_doc'
                    else:
                        return (
                            "Wybacz nie zrozumiałem, wpisz typ dokumentu jako jedno słowo np. 'książka' lub całym "
                            "zdaniem np. 'szukam książki lub dokumentu' (▀̿Ĺ̯▀̿ ̿)")

        if session["stage"] == 'ask_keys':
            if Dialog.isnegation(userText) and userText != 'restart':
                return jsonify([random.choice(DD.dead_end), 'Aby zacząć od nowa wpisz ''restart'' :P'])
            else:
                try:
                    Pkey = Dialog.extract(DD.text_cleaner(userText))
                    if Pkey.essence[0]['keywords']:
                        session["key_logic"] = ['None']
                        session["essence"][session["current_essence"]]['keywords'] = Pkey.essence[0]['keywords']
                        session["essence"][session["current_essence"]]['key_operators'] = Pkey.essence[0]['key_operators']
                        session["stage"] = 'preprocess_key'
                        del Pkey
                    else:
                        return ('Coś poszło nie tak, niestety musisz zrestartować, '
                                'następnym razem spróbuj pełnym zdaniem (▀̿Ĺ̯▀̿ ̿)')
                except:
                    return ('Coś poszło nie tak, niestety musisz zrestartować, '
                            'następnym razem spróbuj pełnym zdaniem (▀̿Ĺ̯▀̿ ̿)')

        # preprocess session["stage"]s
        if session["stage"] == 'ask_solution_UNI':
            question = [random.choice(DD.UNI_found), "(musisz wybrać numerek)"]
            for j in session["UNI_questions"][0][2]:
                question.append(str(j[0]) + ". " + j[2])
            session["stage"] = 'answer_solution_UNI'
            return jsonify(question)

        if session["stage"] == 'ask_solution_SCL':
            session["stage"] = 'answer_solution_SCL'
            if session["uni_type"] == 'docs':
                return ask_solution_SCL(Dialog.doc_logic)
            elif session["uni_type"] == 'keys':
                return ask_solution_SCL(session["key_logic"])

        if session["stage"] == 'answer_solution_UNI':
            solved, solution = service_solution_UNI(session["UNI_questions"][0],
                                                    session["essence"][session["current_essence"]], session["uni_type"],
                                                    userText)
            if not solved:
                return jsonify(solution)
            else:
                session["essence"][session["current_essence"]] = solution
                session["UNI_questions"].pop(0)
                if session["UNI_questions"]:
                    session["stage"] = 'ask_solution_UNI'
                else:
                    if session["uni_type"] == 'docs':
                        session["stage"] = 'preprocess_doc'
                    if session["uni_type"] == 'keys':
                        session["stage"] = 'preprocess_key'

        if session["stage"] == 'answer_solution_SCL':
            if session["uni_type"] == 'docs':
                solved, solution = service_solution_SCL(Dialog.doc_logic, userText)
                if not solved:
                    return solution
                else:
                    Dialog.doc_logic = solution
                    session["stage"] = 'preprocess_doc'

            elif session["uni_type"] == 'keys':
                solved, solution = service_solution_SCL(session["key_logic"], userText)
                if not solved:
                    return solution
                else:
                    session["key_logic"] = solution
                    session["stage"] = 'preprocess_key'


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


def get_keys_from_pd(pd, sess_all):
    all_key = []
    for i, row in pd.iterrows():
        all_key += [x for x in row.keywords if x not in sess_all]

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
