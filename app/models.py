from email.policy import default
from token import OP
from typing import Optional
from . import db

class Dictionary(db.Model):
    __tablename__ = "dictionaries"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    cover_color = db.Column(db.String(20))

    # 初期化メソッド
    def __init__(self, title: Optional[str] = None, cover_color: Optional[str] = None):
        super().__init__()
        if title is not None:
            self.title = title
        if cover_color is not None:
            self.cover_color = cover_color

class Word(db.Model):
    __tablename__ = "words"
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100))
    definition = db.Column(db.String(100))
    line_count = db.Column(db.Integer)
    page_index = db.Column(db.Integer)
    dictionary_id = db.Column(db.Integer, db.ForeignKey("dictionaries.id"))

    # 初期化メソッド
    def __init__(self, word: Optional[str] = None, definition: Optional[str] = None, line_count: Optional[int] = 2, page_index: Optional[int] = None, dictionary_id: Optional[int] = None):
        super().__init__()
        if word is not None:
            self.word = word
        if definition is not None:
            self.definition = definition
        if line_count is not None:
            self.line_count = line_count
        if page_index is not None:
            self.page_index = page_index
        if dictionary_id is not None:
            self.dictionary_id = dictionary_id