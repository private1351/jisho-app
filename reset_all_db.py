"""
JishoJisho: DBを完全リセットして作り直すスクリプト

使い方:
  python reset_all_db.py --seed
  python reset_all_db.py --no-seed

注意:
  --seed を指定しない場合でも、users テーブルを含む全テーブルが drop されます。
  つまりユーザーも含めて全データが消えます。
"""

from __future__ import annotations

import argparse

from app import create_app, db
from set_demo_db import seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="デモデータ（辞書・単語）を投入します")
    parser.add_argument("--no-seed", action="store_true", help="デモデータを投入しません")
    args = parser.parse_args()

    if args.seed and args.no_seed:
        raise SystemExit("同時に --seed と --no-seed は指定できません。")

    # デフォルトは seed しない（=安全側）
    do_seed = args.seed and not args.no_seed
    if not args.seed and not args.no_seed:
        do_seed = False

    app = create_app()
    with app.app_context():
        # 全テーブルを落として作り直す（users も消える）
        db.drop_all()
        db.create_all()

        if do_seed:
            seed(reset=False)

    print("DBを完全リセットしました。")
    if do_seed:
        print("デモデータも投入しました。")


if __name__ == "__main__":
    main()

