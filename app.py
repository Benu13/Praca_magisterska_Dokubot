from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import Dokubot.Dialga as DD
import random
import pandas as pd


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://lukasz:12345@localhost/Dokubot'
app.config['SECRET_KEY'] = 'lukasz1055'
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
            'slot_filler_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/slot_filer/slot_mimic/slot_mimic_medium.h5',
            'slot_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_slot.json',
            'choice_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_choice.json',
            'spacy_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/Spacy_md/',
            'mimic_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/mimic/mimic_smol/mimic_smol.h5',
            'char2tok_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/mimic/mimic_smol/char_tokenizer_mimic_smol.json',
            'misspell_lookup_path': 'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/data/functionalities/lookups/lookup_docs.json'
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
    id = db.Column(db.Integer, primary_key = True)
    key = db.Column(db.String)
    value = db.Column(db.Float)
    document_id = db.Column(db.Integer, db.ForeignKey("Document.id"))
    document = db.relationship("Document", back_populates="keywords")


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', **locals())

@app.route("/get")
def get_bot_response():
    global current_essence, essence_num, UNI_questions, pref_doc_asked, uni_type, stage, stop_flag, found_data
    userText = request.args.get('msg')
    if userText == 'restart':
        Dialog.reset()
        stage = 'start'
        stop_flag = True
        current_essence = 0
        UNI_questions = []
        essence_num = 0
        pref_doc_asked = False
        uni_type = None

        return jsonify([random.choice(DD.retry_responses), random.choice(DD.greet_reactions),
                        random.choice(DD.ask_for_doc)])
    else: stop_flag = False

    while not stop_flag:

        if stage == 'start' and userText != 'restart':
            if Dialog.isgreet(userText):
                return jsonify([random.choice(DD.greet_reactions), random.choice(DD.ask_for_doc)])
            else:
                sentence = Dialog.extract(DD.text_cleaner(userText))
                essence_num = len(sentence.essence)
                Dialog.essence.append(sentence.essence[current_essence])
                stage = 'preprocess_doc'

        if stage == 'preprocess_doc':
            uni_type = 'docs'
            if Dialog.doc_logic[0] != 'CL':
                Dialog.doc_logic = Dialog.LH.solve(Dialog.essence[current_essence]['doc_types'],
                                                   Dialog.essence[current_essence]['doc_operators'])
                if Dialog.doc_logic[0] == 'UNI':
                    UNI_questions = service_question_UNI(Dialog.doc_logic, Dialog.essence[current_essence], 'docs')
                    stage = 'ask_solution_UNI'

                if Dialog.doc_logic[0] == 'NO':
                    Dialog.doc_logic = ('CL',[])

                if Dialog.doc_logic[0] == 'SCL':
                    stage = 'ask_solution_SCL'
            else:
                Dialog.doc_logic_all.append(Dialog.doc_logic)
                stage = 'preprocess_key'

        b = stage
        if stage == 'preprocess_key':
            uni_type = 'keys'
            if Dialog.key_logic[0] != 'CL':

                Dialog.key_logic = Dialog.LH.solve(Dialog.essence[current_essence]['keywords'],
                                                   Dialog.essence[current_essence]['key_operators'])
                if Dialog.key_logic[0] == 'UNI':
                    UNI_questions = service_question_UNI(Dialog.key_logic, Dialog.essence[current_essence], 'keys')
                    stage = 'ask_solution_UNI'

                if Dialog.key_logic[0] == 'NO':
                    Dialog.key_logic = ('CL',[])

                if Dialog.key_logic[0] == 'SCL':
                    stage = 'ask_solution_SCL'
            else:
                Dialog.key_logic_all.append(Dialog.key_logic[1])
                stage = 'check_path'
                #return random.choice(DD.prep_ready)

        if stage == 'check_path':
            uni_type = None

            if not Dialog.doc_pref and not pref_doc_asked:
                Dialog.doc_all_pref(Dialog.essence[current_essence]['doc_types'])
            if not Dialog.doc_pref and not pref_doc_asked:
                stage = 'ask_pref_doc'
                return random.choice(DD.ask_pref_doc)
            elif Dialog.doc_logic[1] and not Dialog.key_logic[1]:
                stage = 'ask_keys'
                return random.choice(DD.ask_for_keys)
            else:
                stage = 'search_narrowing'

        # get data from db and start narrowing
        if stage == 'search_narrowing':
            aa = Dialog
            if not found_data:
                query, all_keys = Dialog.keys_to_query()
                # get query data TODO
                query_got = []
                found_all, count, frequent = Dialog.prep_query_data(query_got, all_keys)

            #ask for custom key if count >100
            #ask to choose if keys < ~30 (keep it or get rid of it)
            #sort score and doc types
            #output
            # print best docs, get info if doc selceted

        # Getting additional information from user
        if stage == 'ask_pref_doc':
            pref_doc_asked = True
            if Dialog.isnegation(userText) and userText != 'restart':
                Dialog.doc_all_flag = True
                stage = 'check_path'
            else:
                Pdoc = Dialog.extract(DD.text_cleaner(userText))
                if Pdoc.essence[0]['doc_types']:
                    Dialog.doc_logic = ['None']
                    Dialog.essence[current_essence]['doc_types'] = Pdoc.essence[0]['doc_types']
                    Dialog.essence[current_essence]['doc_operators'] = Pdoc.essence[0]['doc_operators']
                    del Pdoc
                    stage = 'preprocess_doc'
                else:
                    return('Coś poszło nie tak, niestety musisz zrestartować (▀̿Ĺ̯▀̿ ̿)')

        if stage == 'ask_keys':
            if Dialog.isnegation(userText) and userText != 'restart':
                return jsonify([random.choice(DD.dead_end), 'Aby zacząć od nowa wpisz ''restart'' :P'])
            else:
                Pkey = Dialog.extract(DD.text_cleaner(userText))
                if Pkey.essence[0]['keywords']:
                    Dialog.key_logic = ['None']
                    Dialog.essence[current_essence]['keywords'] = Pkey.essence[0]['keywords']
                    Dialog.essence[current_essence]['key_operators'] = Pkey.essence[0]['key_operators']
                    stage = 'preprocess_key'
                    del Pkey
                else:
                    return ('Coś poszło nie tak, niestety musisz zrestartować (▀̿Ĺ̯▀̿ ̿)')

        # preprocess stages
        if stage == 'ask_solution_UNI':
            question = [random.choice(DD.UNI_found)]
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
            solved, solution = service_solution_UNI(UNI_questions[0], Dialog.essence[current_essence], uni_type, userText)
            if not solved:
                return solution
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

        choices.append((i,num,choice))

    return choices

def service_solution_UNI(choice, essence, op_type, user_choice):
    if op_type == 'docs':
        keys = 'doc_types'
        operators = 'doc_operators'
    if op_type == 'keys':
        keys = 'keywords'
        operators = 'key_operators'

    try:
        uc_int = int(user_choice)
        if uc_int not in range(1, choice[1]):
            return False, random.choice(DD.wrong_choice)
        else:
            essence[operators][choice[0]].logic = choice[2][uc_int - 1][1]
            if choice[2][uc_int - 1][1] == 'OR':
                essence[operators][choice[0]].logic_pl = 'lub'
            if choice[2][uc_int - 1][1] == 'AND':
                essence[operators][choice[0]].logic_pl = 'i'
    except:
        return False, "Opanuj się, tutaj masz tylko wybrać numerek"

    return True, essence

def service_solution_SCL(logic, user_choice):
    try:
        uc_int = int(user_choice)
        if uc_int not in range(1, len(logic[1]) + 1):
            return False, random.choice(DD.wrong_choice)
        else:
            logic = ('CL', logic[1][uc_int - 1][1])
    except:
        return False, "Opanuj się, tutaj masz tylko wybrać numerek"

    return True, logic

if __name__ == '__main__':
    app.run(debug=True)
