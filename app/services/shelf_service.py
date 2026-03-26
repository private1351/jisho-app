from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import Dictionary
from . import dictionary_service


def build_dictionary_shelf_context(query_args, user_id: Optional[int]) -> Dict[str, Any]:
    """
    request.args を渡す。辞書一覧テンプレート用のコンテキストを返す。
    """
    sort = (query_args.get("sort") or "created").strip()
    order_raw = (query_args.get("order") or "").strip()
    if order_raw in ("asc", "desc"):
        order = order_raw
    else:
        order = "desc" if sort == "updated" else "asc"

    selected_colors = [
        c.strip() for c in query_args.getlist("color") if (c or "").strip()
    ]
    fav_only = (query_args.get("fav") or "").strip() == "1"
    mine_only = (query_args.get("mine") or "").strip() == "1"

    dictionaries_all = dictionary_service.visible_dictionaries_query(user_id).order_by(Dictionary.id).all()
    available_colors = sorted({d.cover_color for d in dictionaries_all if d.cover_color})

    q = dictionary_service.visible_dictionaries_query(user_id)
    if mine_only and user_id is not None:
        q = q.filter_by(creator_user_id=user_id)
    if selected_colors:
        q = q.filter(Dictionary.__table__.c.cover_color.in_(selected_colors))  # type: ignore[attr-defined]
    if fav_only:
        q = q.filter_by(is_favorite=True)

    if sort == "color":
        if order == "desc":
            dictionaries = q.order_by(
                Dictionary.__table__.c.cover_color.desc(), Dictionary.id.desc()  # type: ignore[attr-defined]
            ).all()
        else:
            dictionaries = q.order_by(Dictionary.cover_color, Dictionary.id).all()
    elif sort == "updated":
        if order == "asc":
            dictionaries = q.order_by(Dictionary.updated_at, Dictionary.id).all()
        else:
            dictionaries = q.order_by(Dictionary.updated_at.desc(), Dictionary.id.desc()).all()
    else:
        if order == "desc":
            dictionaries = q.order_by(Dictionary.id.desc()).all()
        else:
            dictionaries = q.order_by(Dictionary.id).all()
        sort = "created"

    return {
        "dictionaries": dictionaries,
        "sort": sort,
        "order": order,
        "selected_colors": selected_colors,
        "fav_only": fav_only,
        "mine_only": mine_only,
        "available_colors": available_colors,
    }
