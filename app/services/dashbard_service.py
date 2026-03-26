from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from ..models import Dictionary
from . import dictionary_service


def build_menu_page_context(user_id: int) -> Dict[str, Any]:
    dictionaries: List[Dictionary] = (
        dictionary_service.visible_dictionaries_query(user_id)
        .order_by(Dictionary.updated_at.desc())
        .all()
    )
    created_dictionaries: List[Dictionary] = (
        Dictionary.query.filter_by(creator_user_id=user_id)
        .order_by(Dictionary.updated_at.desc())
        .all()
    )

    created_dictionary_count = len(created_dictionaries)
    favorite_count = len([d for d in dictionaries if d.is_favorite])
    recent_dictionaries = created_dictionaries[:3]
    recommended_dictionary: Optional[Dictionary] = (
        random.choice(dictionaries) if dictionaries else None
    )

    return {
        "created_dictionary_count": created_dictionary_count,
        "favorite_count": favorite_count,
        "recent_dictionaries": recent_dictionaries,
        "recommended_dictionary": recommended_dictionary,
    }
