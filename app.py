from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import Dokubot.Dialga as DD
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://lukasz:12345@localhost/Dokubot'
app.config['SECRET_KEY'] = 'lukasz1055'
db = SQLAlchemy(app)
app.static_folder = 'static'

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
    userText = request.args.get('msg')
    return "SIURY W DZI"


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

if __name__ == '__main__':
    app.run(debug=True)
