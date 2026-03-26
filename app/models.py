from datetime import datetime
from typing import Optional

from sqlalchemy.orm import relationship
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Dictionary(db.Model):
    __tablename__ = "dictionaries"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    cover_color = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)
    creator_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_private = db.Column(db.Boolean, nullable=False, default=False)

    # 初期化メソッド
    def __init__(self, title: Optional[str] = None, cover_color: Optional[str] = None, creator_user_id: Optional[int] = None, is_private: Optional[bool] = False):
        super().__init__()
        if title is not None:
            self.title = title
        if cover_color is not None:
            self.cover_color = cover_color
        if creator_user_id is not None:
            self.creator_user_id = creator_user_id
        if is_private is not None:
            self.is_private = is_private

class Word(db.Model):
    __tablename__ = "words"
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100))
    definition = db.Column(db.Text)
    line_count = db.Column(db.Integer)
    page_index = db.Column(db.Integer)
    dictionary_id = db.Column(db.Integer, db.ForeignKey("dictionaries.id", ondelete="CASCADE"), nullable=False)

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

    def to_dict(self):
        return {
            "id": self.id,
            "word": self.word,
            "definition": self.definition,
            "dictionary_id": self.dictionary_id
        }

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_guest = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)