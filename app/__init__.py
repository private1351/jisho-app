from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager

db: SQLAlchemy = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"  # pyright: ignore

def _ensure_sqlite_columns():
    """
    簡易マイグレーション:
    SQLite は db.create_all() だけだと既存テーブルにカラムを追加できないため、
    必要なカラムが無い場合は ALTER TABLE で追加する。
    """
    # dictionaries テーブルに created_at / updated_at を追加
    cols = db.session.execute(text("PRAGMA table_info(dictionaries)")).fetchall()
    existing = {row[1] for row in cols}  # row[1] = name

    if "created_at" not in existing:
        db.session.execute(text("ALTER TABLE dictionaries ADD COLUMN created_at DATETIME"))
        db.session.execute(text("UPDATE dictionaries SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    if "updated_at" not in existing:
        db.session.execute(text("ALTER TABLE dictionaries ADD COLUMN updated_at DATETIME"))
        db.session.execute(text("UPDATE dictionaries SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
    if "is_favorite" not in existing:
        # SQLite は BOOLEAN 型が実質 INTEGER 扱いになるため 0/1 で運用
        db.session.execute(text("ALTER TABLE dictionaries ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0"))
        db.session.execute(text("UPDATE dictionaries SET is_favorite = 0 WHERE is_favorite IS NULL"))

    db.session.commit()

def create_app() -> Flask:
    app: Flask = Flask(__name__)

    # データベース設定（instance/jishojisho.db を利用）
    import os
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.abspath(os.path.join(app.instance_path, 'jishojisho.db')).replace('\\', '/')
    app.config['SECRET_KEY'] = 'secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes
        from .models import Dictionary, Word
        db.create_all()
        _ensure_sqlite_columns()

    # ルーティング登録
    from app.routes import main
    app.register_blueprint(main)

    return app
