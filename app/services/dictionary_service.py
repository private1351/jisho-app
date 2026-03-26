from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_

from .. import db
from ..models import Dictionary, Word, User

# 1ページに収まる表示行数の上限（add_words.js のサーバー側と一致）
MAX_LINES_PER_PAGE = 25


def visible_dictionaries_query(user_id: Optional[int]):
    """
    可視性ルール:
    - public（is_private=False）は全員に表示
    - private（is_private=True）は作成者本人にのみ表示（=辞書棚でのみ使う想定）
    """
    q = Dictionary.query
    if user_id is None:
        return q.filter_by(is_private=False)
    # 型チェッカー対策のため __table__.c を使って条件式を作る
    return q.filter(
        or_(
            Dictionary.__table__.c.is_private == 0,  # type: ignore[attr-defined]
            Dictionary.__table__.c.creator_user_id == user_id,  # type: ignore[attr-defined]
        )
    )


def reflow_dictionary_words(dictionary_id: int) -> None:
    """
    辞書内の全単語をID順に並べ、左ページ→右ページ→次の見開き…の順で詰め直して
    page_indexを振り直す(スクロールせずページ送りするための整形)
    """
    words = Word.query.filter_by(dictionary_id=dictionary_id).order_by(Word.id).all()
    page_index = 0
    left_lines = 0
    right_lines = 0

    for word in words:
        lines = 1 + (word.line_count or 2)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            word.page_index = page_index
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            word.page_index = page_index
            right_lines += lines
        else:
            page_index += 1
            left_lines = lines
            right_lines = 0
            word.page_index = page_index

    db.session.commit()


def split_words_into_spread(words: List[Word]) -> Tuple[List[Word], List[Word]]:
    left_words: List[Word] = []
    right_words: List[Word] = []
    left_lines = 0
    right_lines = 0

    for word in words:
        lines = 1 + (word.line_count or 2)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            left_words.append(word)
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            right_words.append(word)
            right_lines += lines
        else:
            right_words.append(word)

    return left_words, right_words


def page_navigation_flags(dictionary_id: int, page: int) -> Tuple[bool, bool, int, int]:
    prev_page = page - 1 if page > 0 else 0
    next_page = page + 1
    has_prev = page > 0 and Word.query.filter_by(
        dictionary_id=dictionary_id, page_index=prev_page
    ).first() is not None
    has_next = Word.query.filter_by(
        dictionary_id=dictionary_id, page_index=next_page
    ).first() is not None
    return has_prev, has_next, prev_page, next_page


def build_add_words_page_context(dictionary_id: int, page: int) -> Optional[Dict[str, Any]]:
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return None

    reflow_dictionary_words(dictionary_id)
    words = (
        Word.query.filter_by(dictionary_id=dictionary_id, page_index=page)
        .order_by(Word.id)
        .all()
    )
    has_prev, has_next, _, _ = page_navigation_flags(dictionary_id, page)
    left_words, right_words = split_words_into_spread(words)

    return {
        "dictionary": dictionary,
        "cover_color": dictionary.cover_color,
        "page": page,
        "has_prev": has_prev,
        "has_next": has_next,
        "left_words": left_words,
        "right_words": right_words,
    }


def build_view_words_page_context(dictionary_id: int, page: int) -> Optional[Dict[str, Any]]:
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return None

    creator = User.query.get(dictionary.creator_user_id)
    creator_user_name = creator.username if creator else ""

    reflow_dictionary_words(dictionary_id)
    words = (
        Word.query.filter_by(dictionary_id=dictionary_id, page_index=page)
        .order_by(Word.id)
        .all()
    )
    has_prev, has_next, prev_page, next_page = page_navigation_flags(dictionary_id, page)
    left_words, right_words = split_words_into_spread(words)

    return {
        "dictionary": dictionary,
        "creator_user_name": creator_user_name,
        "cover_color": dictionary.cover_color,
        "page": page,
        "prev_page": prev_page,
        "next_page": next_page,
        "has_prev": has_prev,
        "has_next": has_next,
        "left_words": left_words,
        "right_words": right_words,
    }


def save_words_bulk(
    dictionary_id: int, page_index: int, words_payload: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    戻り値: (成功, エラーメッセージ, json用dict)
    """
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return False, "辞書が見つかりませんでした。", None

    updated = 0
    created = 0
    touched_ids: List[int] = []

    for item in words_payload:
        word_id = item.get("id")
        word_text = (item.get("word") or "").strip()
        definition_text = (item.get("definition") or "").strip()
        line_count = item.get("line_count") or 2

        if not word_id and not word_text:
            continue

        if word_id:
            word = Word.query.get(word_id)
            if word and word.dictionary_id == dictionary_id:
                word.word = word_text
                word.definition = definition_text
                word.line_count = line_count
                word.page_index = page_index
                updated += 1
                touched_ids.append(word.id)
        else:
            new_word = Word(
                word=word_text,
                definition=definition_text,
                dictionary_id=dictionary_id,
                line_count=line_count,
                page_index=page_index,
            )
            db.session.add(new_word)
            db.session.flush()
            created += 1
            touched_ids.append(new_word.id)

    db.session.commit()
    reflow_dictionary_words(dictionary_id)

    target_page = page_index
    if touched_ids:
        first = (
            Word.query.filter_by(dictionary_id=dictionary_id)
            .filter(Word.id.in_(touched_ids))
            .order_by("page_index", "id")
            .first()
        )
        if first:
            target_page = first.page_index

    return True, None, {
        "success": True,
        "updated": updated,
        "created": created,
        "page_index": target_page,
    }


def delete_word_in_dictionary(dictionary_id: int, word_id: int) -> Tuple[bool, Optional[str]]:
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return False, "辞書が見つかりませんでした。"

    word = Word.query.get(word_id)
    if not word or word.dictionary_id != dictionary_id:
        return False, "単語が見つかりませんでした。"

    db.session.delete(word)
    db.session.commit()
    reflow_dictionary_words(dictionary_id)
    return True, None


def toggle_dictionary_favorite(
    dictionary_id: int, data: Dict[str, Any]
) -> Tuple[bool, Optional[str], Optional[bool]]:
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return False, "辞書が見つかりませんでした。", None

    if "favorite" in data:
        dictionary.is_favorite = bool(data.get("favorite"))
    else:
        dictionary.is_favorite = not bool(getattr(dictionary, "is_favorite", False))

    db.session.commit()
    return True, None, bool(dictionary.is_favorite)


def create_dictionary(title: str, cover_color: str, creator_user_id: int, is_private: bool) -> Dictionary:
    new_dictionary = Dictionary(title=title, cover_color=cover_color, creator_user_id=creator_user_id, is_private=is_private)
    db.session.add(new_dictionary)
    db.session.commit()
    return new_dictionary


def update_dictionary_metadata(
    dictionary: Dictionary, new_title: str, new_color: str, new_is_private: bool
) -> bool:
    """変更があればコミットして True。無ければ False。"""
    if dictionary.title == new_title and dictionary.cover_color == new_color and dictionary.is_private == new_is_private:
        return False
    dictionary.title = new_title
    dictionary.cover_color = new_color
    dictionary.is_private = new_is_private
    db.session.commit()
    return True


def delete_dictionary_by_id(dictionary: Dictionary) -> None:
    db.session.delete(dictionary)
    db.session.commit()


def list_words_for_dict(dict_id: Any) -> List[Word]:
    return Word.query.filter(Word.dictionary_id == dict_id).all()


def list_public_dictionaries() -> List[Dictionary]:
    return Dictionary.query.filter_by(is_private=False).order_by(Dictionary.id).all()
