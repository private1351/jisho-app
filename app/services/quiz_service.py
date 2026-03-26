from __future__ import annotations

import random
from typing import Dict, List

from ..models import Word


def generate_incorrect_choices(words: List[Word]) -> Dict[int, List[str]]:
    result: Dict[int, List[str]] = {}
    definitions = [w.definition or "" for w in words]
    for w in words:
        others = [d for d in definitions if d != (w.definition or "")]
        if len(others) >= 2:
            result[w.id] = random.sample(others, 2)
        elif others:
            result[w.id] = (random.sample(others, len(others)) + others * 2)[:2]
        else:
            result[w.id] = ["(選択肢)", "(選択肢)"]
    return result


def build_choice_quiz_data(words: List[Word]) -> List[dict]:
    incorrect_choices = generate_incorrect_choices(words)
    quiz_data: List[dict] = []
    for word in words:
        choices = incorrect_choices[word.id] + [word.definition]
        random.shuffle(choices)
        quiz_data.append(
            {
                "word": word.word,
                "correct": word.definition,
                "choices": choices,
            }
        )
    random.shuffle(quiz_data)
    return quiz_data
