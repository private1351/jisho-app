from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import Dictionary, Word, User
from .form import LoginForm, RegistrationForm
from . import login_manager

main = Blueprint('main', __name__)

# 1ページに収まる表示行数の上限
MAX_LINES_PER_PAGE = 25

def reflow_dictionary_words(dictionary_id: int):
    """
    辞書内の全単語をID順に並べ、左ページ→右ページ→次の見開き…の順で詰め直して
    page_indexを振り直す(スクロールせずページ送りするための整形)
    """
    words = Word.query.filter_by(dictionary_id=dictionary_id).order_by(Word.id).all()
    page_index = 0
    left_lines = 0
    right_lines = 0

    for word in words:
        lines = 1 + (word.line_count or 2)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            word.page_index = page_index
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            word.page_index = page_index
            right_lines += lines
        else:
            page_index += 1
            left_lines = lines
            right_lines = 0
            word.page_index = page_index

    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('ログインしました')
            return redirect(url_for('main.index'))
        else:
            flash('ユーザー名またはパスワードが間違っています')
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('登録が完了しました')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    return render_template('menu.html')

@main.route('/create-dictionary', methods=['GET', 'POST'])
def create_dictionary():
    cover_colors = ['#773333', '#334477', '#335544', '#333333', '#C56700']

    if request.method == 'POST':
        # フォームデータを取得
        title = request.form.get('cover-title', '').strip()
        cover_color = request.form.get('cover-color', '')

        # バリデーション
        if not title:
            return render_template('create_dictionary.html',
                                    cover_colors=cover_colors,
                                    error='辞書名を入力してください')

        # データベースに保存
        new_dictionary = Dictionary(title=title, cover_color=cover_color)
        db.session.add(new_dictionary)
        db.session.commit()

        # 保存後、単語登録ページにリダイレクト（作成した辞書のIDを渡す）
        return redirect(url_for('main.add_words', dictionary_id=new_dictionary.id, page=0))

    return render_template('create_dictionary.html', cover_colors=cover_colors)

# 単語登録ページ
@main.route('/add-words/<int:dictionary_id>/<int:page>')
def add_words(dictionary_id, page):
    # 指定された辞書を取得
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return redirect(url_for('main.index'))

    # 表示前に全体を詰め直して「左が埋まったら右→次ページ」を常に維持する
    reflow_dictionary_words(dictionary_id)

    cover_color = dictionary.cover_color
    words = (Word.query
            .filter_by(dictionary_id=dictionary_id, page_index=page)
            .order_by(Word.id)
            .all())

    left_words = []
    right_words = []

    left_lines = 0
    right_lines = 0

    for word in words:
        lines = 1 + (word.line_count or 2)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            left_words.append(word)
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            right_words.append(word)
            right_lines += lines
        else:
            # データが溢れている場合(基本はreflowで発生しない想定)
            right_words.append(word)

    return render_template('add_words.html',
                            dictionary=dictionary,
                            cover_color=cover_color,
                            page=page,
                            left_words=left_words,
                            right_words=right_words)

# 単語の一括保存API(手動保存用)
@main.route('/add-words/<int:dictionary_id>/save-words', methods=['POST'])
def save_words(dictionary_id):
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return jsonify({'success': False, 'error': '辞書が見つかりませんでした。'}), 404

    data = request.get_json() or {}
    words = data.get('words') or []
    page_index = data.get('page_index', 0)

    updated = 0
    created = 0
    touched_ids = []

    for item in words:
        word_id = item.get('id')
        word_text = (item.get('word') or '').strip()
        definition_text = (item.get('definition') or '').strip()
        line_count = item.get('line_count') or 2

        # 新規は「単語」が空なら保存しない(空行を増やさないため)
        if not word_id and not word_text:
            continue

        if word_id:
            word = Word.query.get(word_id)
            if word and word.dictionary_id == dictionary_id:
                word.word = word_text
                word.definition = definition_text
                word.line_count = line_count
                word.page_index = page_index
                updated += 1
                touched_ids.append(word.id)
        else:
            new_word = Word(word=word_text,
                            definition=definition_text,
                            dictionary_id=dictionary_id,
                            line_count=line_count,
                            page_index=page_index)
            db.session.add(new_word)
            db.session.flush()  # id確定
            created += 1
            touched_ids.append(new_word.id)

    db.session.commit()

    # 全体を詰め直して「左が埋まったら右→次ページ」の形に整形
    reflow_dictionary_words(dictionary_id)

    # 保存後にどのページにいるべきか（触った単語があるページ）を返す
    target_page = page_index
    if touched_ids:
        first = (Word.query
                .filter(Word.dictionary_id == dictionary_id, Word.id.in_(touched_ids))
                .order_by('page_index', 'id')
                .first())
        if first:
            target_page = first.page_index

    return jsonify({'success': True, 'updated': updated, 'created': created, 'page_index': target_page})

# 単語削除API（1単語ずつ削除）
@main.route('/add-words/<int:dictionary_id>/delete-word/<int:word_id>', methods=['POST'])
def delete_word(dictionary_id, word_id):
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return jsonify({'success': False, 'error': '辞書が見つかりませんでした。'}), 404

    word = Word.query.get(word_id)
    if not word or word.dictionary_id != dictionary_id:
        return jsonify({'success': False, 'error': '単語が見つかりませんでした。'}), 404

    db.session.delete(word)
    db.session.commit()
    # 削除した分を詰めて再整形
    reflow_dictionary_words(dictionary_id)
    return jsonify({'success': True})

# お気に入り切替API（辞書棚用）
@main.route('/dictionary-shelf/favorite/<int:dictionary_id>', methods=['POST'])
def toggle_favorite(dictionary_id):
    dictionary = Dictionary.query.get(dictionary_id)
    if not dictionary:
        return jsonify({'success': False, 'error': '辞書が見つかりませんでした。'}), 404

    data = request.get_json(silent=True) or {}
    # favorite が渡されたらそれを採用、無ければトグル
    if 'favorite' in data:
        dictionary.is_favorite = bool(data.get('favorite'))
    else:
        dictionary.is_favorite = not bool(getattr(dictionary, 'is_favorite', False))

    db.session.commit()
    return jsonify({'success': True, 'is_favorite': bool(dictionary.is_favorite)})

# 辞書一覧ページ
@main.route('/dictionary-shelf')
def dictionary_shelf():
    # sort:
    # - created: 作成順（=id順）
    # - color  : カバー色（cover_color）順
    # - updated: 更新日（updated_at）順
    sort = (request.args.get('sort') or 'created').strip()
    # order:
    # - asc : 昇順
    # - desc: 降順
    order_raw = (request.args.get('order') or '').strip()
    if order_raw in ('asc', 'desc'):
        order = order_raw
    else:
        # デフォルト: 更新日は新しい順、それ以外は昇順
        order = 'desc' if sort == 'updated' else 'asc'
    # color（複数指定可）:
    # - color パラメータを複数渡す: ?color=#773333&color=#334477
    # - 1つも無ければ絞り込みなし
    selected_colors = [c.strip() for c in request.args.getlist('color') if (c or '').strip()]
    # fav:
    # - 1: お気に入りのみ
    fav_only = (request.args.get('fav') or '').strip() == '1'

    # フィルタUI用: 既存辞書の色一覧（DBに存在する色だけ出す）
    dictionaries_all = Dictionary.query.order_by(Dictionary.id).all()
    available_colors = sorted({d.cover_color for d in dictionaries_all if d.cover_color})

    q = Dictionary.query
    if selected_colors:
        # NOTE: 型チェッカーが SQLAlchemy の属性を str 扱いするため、ここは抑制する
        q = q.filter(Dictionary.__table__.c.cover_color.in_(selected_colors))  # pyright: ignore
    if fav_only:
        q = q.filter_by(is_favorite=True)

    if sort == 'color':
        # cover_color は '#RRGGBB' を想定。文字列順になるが色のグルーピング用途には十分。
        if order == 'desc':
            dictionaries = q.order_by(Dictionary.__table__.c.cover_color.desc(), Dictionary.id.desc()).all()  # pyright: ignore
        else:
            dictionaries = q.order_by(Dictionary.cover_color, Dictionary.id).all()
    elif sort == 'updated':
        # updated_at は辞書の最終更新時刻（単語の保存/削除時に更新）
        if order == 'asc':
            dictionaries = q.order_by(Dictionary.updated_at, Dictionary.id).all()
        else:
            dictionaries = q.order_by(Dictionary.updated_at.desc(), Dictionary.id.desc()).all()
    else:
        if order == 'desc':
            dictionaries = q.order_by(Dictionary.id.desc()).all()
        else:
            dictionaries = q.order_by(Dictionary.id).all()
        sort = 'created'

    return render_template(
        'dictionary_shelf.html',
        dictionaries=dictionaries,
        sort=sort,
        order=order,
        selected_colors=selected_colors,
        fav_only=fav_only,
        available_colors=available_colors,
    )

#; DB全削除(開発用)
@main.route('/delete-db')
def delete_db():
    db.drop_all()
    db.create_all()
    return redirect(url_for('main.index'))