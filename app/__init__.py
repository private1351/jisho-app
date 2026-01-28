from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy()

def create_app() -> Flask:
    app: Flask = Flask(__name__)

    # データベース設定
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jishojisho.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from . import routes
        from .models import Dictionary, Word
        db.create_all()

    # ルーティング登録
    from app.routes import main
    app.register_blueprint(main)

    return app
