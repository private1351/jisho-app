import sqlite3
import os

db_path = 'instance/jishojisho.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル一覧を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("=== テーブル一覧 ===")
    for table in tables:
        print(f"- {table[0]}")
    print()

    # 各テーブルの内容を表示
    for table in tables:
        table_name = table[0]
        print(f"=== {table_name} テーブルの内容 ===")
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()

        # カラム名を取得
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"カラム: {', '.join(column_names)}")
        print()

        if rows:
            for row in rows:
                print(row)
        else:
            print("(データなし)")
        print()

    conn.close()
else:
    print(f"データベースファイルが見つかりません: {db_path}")









