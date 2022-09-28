import fitz
import os
import re
import string
import hashlib
import spacy
from typing import Union
from unidecode import unidecode


def get_rect(page_size, margin_list):
    # margin _list = left_margin, right_margin, top_margin, bottom_margin
    a4_size = [210, 297]

    lm = round(page_size[0] * margin_list[0] / a4_size[0])
    rm = round(page_size[0] * margin_list[1] / a4_size[0])
    tm = round(page_size[1] * margin_list[2] / a4_size[1])
    bm = round(page_size[1] * margin_list[3] / a4_size[1])

    # print(lm,tm,page_size[0]-rm, page_size[1]-bm)

    return fitz.Rect(lm, tm, page_size[0] - rm, page_size[1] - bm)


def pdf_to_text(path: Union[str, bytes], save: bool = False, save_path: str = None, save_name: str = None,
                omfp: int = 0, omlp: int = 0, margins: bool = False, margin_size: list = []) -> (str, dict):

    # Convert PDF document into text
    # Input:
    # PATH: string/bytes - string containing non-relative path to .PDF document or bytes of pdf file
    # save: boolean - switch for saving plain text to .txt file with the name of .pdf document
    # save_path: string - path to where .txt file will be saved to, if none: save_path=path
    # save_name: string - name of saved .txt file, if none: save_name=filename
    # omfp: int - set to n to omit first n pages
    # omlp: int - set to m to omit last m pages
    # margins: bool - set to True do remove text beyond margins(eg. header, footer)
    # margin_size: list[float] - size of margin in mm [left_margin, right_margin, top_margin, bottom_margin]
    #
    # Output:
    # (string: text extracted from .PDF document, dict: metadata extracted from document)

    rect = None

    if save:
        if save_path is None:
            save_path, tail = os.path.split(path)
        if save_name is None:
            base=os.path.basename(path)
            save_name = os.path.splitext(base)[0]

    # Open pdf with fitz (PyMuPDF)

    if type(path) is bytes:
        doc = fitz.open(stream=path, filetype="pdf")
    else:
        doc = fitz.open(path)

    # Extract metadata
    metadata = doc.metadata

    pages = doc.page_count - omlp - 1  # Pages number - 1 for index and - omlp for omiting last m pages

    # Open .txt if saving=true
    if save:
        out = open(save_path + "/" + save_name + ".txt", "wb")  # open text output

    # Iterate through pages and extract data
    text = ""
    for page in doc:  # iterate throught document pages
        if (page.number < omfp or page.number > pages):
            # print('omited')
            pass
        else:
            if margins:
                page_size = [page.rect[2], page.rect[3]]
                rect = get_rect(page_size, margin_size)

            text = text + page.get_text(clip=rect) # get plain text (is in UTF-8)

            if save:
                out.write(text)  # write text of page
                out.write(bytes((12,)))  # write page delimiter (form feed 0x0C)

    if save:
        out.close()  # close .txt file


    # Return data
    return text, metadata


def text_cleaner(text: str) -> str:
    # Remove: punctuations, URLs, numbers, unnecesary or unknown symbols
    # Do: lower case, connect words split by new line

    # Input:
    # text: string - user specified text to clean
    #
    # Output:
    # Cleaned text


    text = text.replace(u'-\n', u'') # connect words split by new line
    text = re.sub(r"\S*https?:\S*", "", text) # remove links
    text = re.sub(r"\S*@?:\S*", "", text)  # remove links

    #text = text.translate(str.maketrans('', '', string.digits)) # remove digits
    #text = text.translate(str.maketrans('', '','!@#$%^&*()[]{};/<>`~-=_+|')) # remove punctuation
    text = text.replace(r"!?@#$%^&*()[]{};/<>\|`~-=_+", "")
    text = text.replace(r",", ", ")
    # text = text.replace(u'\n', u' ')
    #text = text.replace(u'�', u' ') # custom
    #text = text.replace(u'–', u' ') # remove - because it's not in string.punctuation
    text = text.lower() # lowercase text
    text = ' '.join(text.split()) # remove unnecessary whitespaces
    return text


def split_to_sentence(text: str):
    # Split text into sentences based on "."

    text = text.replace(u'-\n', u'') # Connect lines broken mid-word with "-" sign
    text = text.replace(u'\n', u' ') # Delete newline
    return re.split('\. ',text)



def remove_stopwords(text: Union[list[str],spacy.tokens.doc.Doc], stopwords: set[str] = None,
                     min_length: int = 0, pos_tags: list[str] = []) -> list[str]:
    # remove stopwords from custom tokenized text or spacy document class
    # Input:
    # text: Union[list[str],spacy.tokens.doc.Doc] - tokenized text or spacy doc class
    # stopwords: set[str] - set of stopwords, obligatory if text not a spacy class
    # min_length: int - minimum length of word to leave in text default=0
    # pos_tags: list[str] - list of POS Tags from spacy pipeline to remove (only for spacy class with tagger)
    # Output:
    # clean_text: list[str] - list of tokens

    clean_tokens = []
    if type(text) is spacy.tokens.doc.Doc:
        for token in text:
            if not token.is_stopword and len(token.lemma_) > min_length and token.tag_ not in pos_tags:
                clean_tokens.append(token.lemma_)
    else:
        try:
            for token in text:
                if token not in stopwords and len(token) > min_length:
                    clean_tokens.append(token)
        except TypeError:
            print("Argument 'stopwords' must be passed when not using spacy class.")

    return clean_tokens


def get_dkey(text: str, hash_type: str = 'md5') -> str:
    # Create original document key by hashing it's content
    # Input:
    # text:str - text to hash
    # hash_type: type of hash
    # Output:
    # hash of document in hexadecimal value

    # TODO - differnt hash types
    return hashlib.md5(text.encode()).hexdigest()

