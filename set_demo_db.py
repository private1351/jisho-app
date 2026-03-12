"""
JishoJisho: デモデータ投入スクリプト

使い方:
  python set_demo_db.py            # 既存データは残したまま、足りない分だけ追加（重複は作りにくい）
  python set_demo_db.py --reset    # DBを全削除してからデモデータを投入（テスト用）
"""

from __future__ import annotations

import argparse
from typing import Sequence

from app import create_app, db
from app.models import Dictionary, Word


def _add_words(dictionary_id: int, page_index: int, items: Sequence[tuple[str, str, int]]):
    for w, d, line_count in items:
        db.session.add(
            Word(
                word=w,
                definition=d,
                line_count=line_count,
                page_index=page_index,
                dictionary_id=dictionary_id,
            )
        )


def seed(reset: bool) -> None:
    if reset:
        db.drop_all()
        db.create_all()

    # すでに辞書があるなら「追加」モード（同名なら作らない）
    existing_titles = {d.title for d in Dictionary.query.all()}

    demo_dicts = [
        # 英語系
        ("(英)食べ物", "#C56700"),
        ("(英)動物", "#C56700"),
        ("(英)色", "#C56700"),
        ("(英)体の部位", "#C56700"),
        ("(英)天気", "#C56700"),

        # 歴史・地理系
        ("日本史", "#335544"),
        ("地理", "#335544"),

        # IT系
        ("IT用語", "#333333"),

        # 算数・理科系
        ("数学", "#334477"),
        ("物理", "#334477"),
        ("化学", "#334477"),
        ("生物", "#334477"),

        # 国語系
        ("文学", "#773333"),
        ("漢字", "#773333"),
    ]

    created_dicts: list[Dictionary] = []
    for title, color in demo_dicts:
        if title in existing_titles:
            continue
        d = Dictionary(title=title, cover_color=color)
        db.session.add(d)
        created_dicts.append(d)

    db.session.commit()

    # titleから確実にIDを引く
    dict_by_title = {d.title: d for d in Dictionary.query.all()}

    # ===============================
    # まとめてデモ単語投入
    # ===============================

    bulk_words = {
        "(英)食べ物": [
            ("bread", "パン", 2),
            ("rice", "ごはん", 2),
            ("milk", "牛乳", 2),
        ],

        "(英)動物": [
            ("dog", "犬", 2),
            ("cat", "猫", 2),
            ("elephant", "象", 2),
        ],

        "(英)色": [
            ("red", "赤", 2),
            ("blue", "青", 2),
            ("yellow", "黄色", 2),
        ],

        "(英)体の部位": [
            ("hand", "手", 2),
            ("eye", "目", 2),
            ("head", "頭", 2),
        ],

        "(英)天気": [
            ("sunny", "晴れの", 2),
            ("rainy", "雨の", 2),
            ("cloudy", "くもりの", 2),
        ],
        "日本史": [
            ("大化の改新", "645年に始まった政治改革。", 2),
            ("鎌倉幕府", "源頼朝が開いた武家政権。", 2),
            ("明治維新", "近代国家への改革。", 2),
        ],
        "地理": [
            ("赤道", "地球を南北に分ける線。", 2),
            ("季節風", "季節で風向きが変わる風。", 2),
            ("人口密度", "単位面積あたりの人口。", 2),
        ],
        "IT用語": [
            ("API", "アプリ同士をつなぐ仕組み。", 2),
            ("DB", "データを保存する仕組み。", 2),
            ("HTTP", "Web通信のルール。", 2),
        ],
        "数学": [
            ("比例", "一定の割合で増減する関係。", 2),
            ("平方根", "2乗して元の数になる数。", 2),
            ("確率", "起こる可能性の度合い。", 2),
        ],
        "物理": [
            ("速度", "単位時間あたりの移動距離。", 2),
            ("力", "物体の運動を変える作用。", 2),
            ("エネルギー", "仕事をする能力。", 2),
        ],
        "化学": [
            ("原子", "物質を構成する最小単位。", 2),
            ("分子", "原子が結合したもの。", 2),
            ("化学反応", "物質が変化すること。", 2),
        ],
        "生物": [
            ("細胞", "生物の基本単位。", 2),
            ("光合成", "植物が光で養分を作る働き。", 2),
            ("DNA", "遺伝情報を持つ物質。", 2),
        ],
        "文学": [
            ("随筆", "体験や感想を自由に書いた文章。", 2),
            ("比喩", "たとえを用いた表現。", 2),
            ("主題", "作品の中心テーマ。", 2),
        ],
        "漢字読み": [
            ("曖昧", "あいまい", 2),
            ("顕著", "けんちょ", 2),
            ("憂鬱", "ゆううつ", 2),
        ],
    }

    for title, items in bulk_words.items():
        if title in dict_by_title:
            d = dict_by_title[title]
            if reset or Word.query.filter_by(dictionary_id=d.id).count() == 0:
                _add_words(d.id, 0, items)

    db.session.commit()

    # routes側の「詰め直し」は表示/保存時にも動くので、
    # ここでは page_index は仮でOK（テストで保存すると整形される）。


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="DBを全削除してデモデータを投入します")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        seed(reset=args.reset)

    print("デモデータを投入しました。")


if __name__ == "__main__":
    main()


