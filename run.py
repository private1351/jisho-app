import os
import sys

# プロジェクトルート（run.py があるフォルダ）をカレントにする
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5002, host="127.0.0.1")