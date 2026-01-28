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
        ("英単語", "#334477"),
        ("日本史", "#335544"),
        ("IT用語", "#333333"),
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

    # 単語は「ページ送り」動作が確認できるよう、量を少し入れる
    if "英単語" in dict_by_title:
        d = dict_by_title["英単語"]
        if reset or Word.query.filter_by(dictionary_id=d.id).count() == 0:
            # 2見開き（左右）= 1ページIndexあたり MAX_LINES_PER_PAGE*2 相当なので、
            # ここでは十分な件数を入れて「次のページ」確認ができるようにする。
            core_items: list[tuple[str, str, int]] = [
                ("apple", "りんご", 2),
                ("banana", "バナナ", 2),
                ("cat", "猫", 2),
                ("dog", "犬", 2),
                ("efficient", "効率的な", 2),
                ("implement", "実装する", 2),
                ("validate", "検証する", 2),
                ("persistent", "永続的な", 2),
                ("robust", "堅牢な", 2),
                ("refactor", "リファクタリングする", 2),
                ("architecture", "設計", 2),
                ("constraint", "制約", 2),
                ("optimize", "最適化する", 2),
                ("iterate", "反復する", 2),
                ("feature", "機能", 2),
                ("release", "リリース", 2),
                ("debug", "デバッグする", 2),
                ("commit", "コミットする", 2),
                ("merge", "マージする", 2),
                ("branch", "ブランチ", 2),
            ]

            # 追加でダミー単語を作って複数ページを確実に作る（60件）
            generated: list[tuple[str, str, int]] = []
            for i in range(1, 61):
                line_count = 2 if (i % 3) else 3  # たまに少し長めにして行数の挙動も確認
                generated.append((f"demo_word_{i:02d}", f"デモ意味_{i:02d}", line_count))

            _add_words(
                d.id,
                page_index=0,
                items=[
                    *core_items,
                    *generated,
                ],
            )

    if "日本史" in dict_by_title:
        d = dict_by_title["日本史"]
        if reset or Word.query.filter_by(dictionary_id=d.id).count() == 0:
            _add_words(
                d.id,
                page_index=0,
                items=[
                    ("大化の改新", "645年。中大兄皇子・中臣鎌足らが進めた政治改革。", 3),
                    ("平安京遷都", "794年。桓武天皇。", 2),
                    ("鎌倉幕府", "1192年（通説）。源頼朝。", 2),
                    ("応仁の乱", "1467年〜1477年。戦国時代の契機。", 3),
                ],
            )

    if "IT用語" in dict_by_title:
        d = dict_by_title["IT用語"]
        if reset or Word.query.filter_by(dictionary_id=d.id).count() == 0:
            _add_words(
                d.id,
                page_index=0,
                items=[
                    ("API", "アプリ同士がやりとりするための窓口。", 2),
                    ("DB", "データベース。情報を保存する仕組み。", 2),
                    ("SQL", "DBを操作する言語。", 2),
                    ("HTTP", "Web通信のプロトコル。", 2),
                    ("JSON", "データ表現フォーマット。", 2),
                ],
            )

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


