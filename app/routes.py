import random
from typing import List, Dict
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

@main.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました')
    return redirect(url_for('main.login'))

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

#; 辞書の編集
@main.route('/update-dictionary/<int:dictionary_id>', methods=['GET', 'POST'])
def update_dictionary(dictionary_id):
    cover_colors = ['#773333', '#334477', '#335544', '#333333', '#C56700']
    dictionary = Dictionary.query.get_or_404(dictionary_id)
    original_title = dictionary.title
    original_color = dictionary.cover_color
    if request.method == 'POST':
        new_title = request.form.get('cover-title', '').strip()
        new_color = request.form.get('cover-color', '')
        # バリデーション
        if not new_title:
            return render_template(
                'dictionary_detail.html',
                dictionary=dictionary,
                cover_colors=cover_colors,
                error='辞書名を入力してください',
            )
        if original_title != new_title or original_color != new_color:
            dictionary.title = new_title
            dictionary.cover_color = new_color
            db.session.commit()
            return redirect(url_for('main.update_dictionary', dictionary_id=dictionary.id))
    return render_template('dictionary_detail.html', dictionary=dictionary, cover_colors=cover_colors)

#; 辞書の削除
@main.route('/delete-dictionary/<int:dictionary_id>', methods=['POST'])
def delete_dictionary(dictionary_id):
    dictionary = Dictionary.query.get_or_404(dictionary_id)
    db.session.delete(dictionary)
    db.session.commit()
    return redirect(url_for('main.dictionary_shelf'))

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
        q = q.filter(Dictionary.__table__.c.cover_color.in_(selected_colors))  # pyright: ignore
    if fav_only:
        q = q.filter_by(is_favorite=True)

    if sort == 'color':
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

# クイズメインページ
@main.route('/quiz-menu')
def quiz_menu():
    dictionaries = Dictionary.query.all()
    return render_template('quiz_menu.html', dictionaries=dictionaries)

# クイズプレイページ
# 1: 択一
# 2: 記述
@main.route('/quiz-play/<dict_id>/<int:quiz_type>')
def quiz_play(dict_id, quiz_type):
    words = Word.query.filter(Word.dictionary_id == dict_id).all()
    dict = Dictionary.query.filter(Dictionary.id == dict_id).first()
    dict_name = dict.title if dict else ""
    # 択一式クイズ
    if quiz_type == 1:
        incorrect_choices = generate_incorrect_choices(words)
        quiz_data = []
        for word in words:
            choices = incorrect_choices[word.id] + [word.definition]
            random.shuffle(choices)
            quiz_data.append({
                "word": word.word,
                "correct": word.definition,
                "choices": choices
            })
        random.shuffle(quiz_data)
        return render_template(
            'quiz_play_choice.html',
            quiz_data=quiz_data,
            dict_id=dict_id,
            dict_name=dict_name,
            quiz_type=quiz_type
        )
    # 記述式クイズ
    elif quiz_type == 2:
        return render_template('quiz_play_description.html', dict_id=dict_id, quiz_type=quiz_type, dict_name=dict_name)
    else:
        return redirect(url_for('main.quiz_menu'))

def generate_incorrect_choices(words: List[Word]) -> Dict[int, List[str]]:
    result: Dict[int, List[str]] = {}
    definitions = [w.definition or "" for w in words]
    for w in words:
        others = [d for d in definitions if d != (w.definition or "")]
        # 3択問題にするため、誤選択肢は常に2つ用意する
        if len(others) >= 2:
            result[w.id] = random.sample(others, 2)
        elif others:
            # 誤選択肢候補が1つしかない場合は、それを複製して2つにする
            # 例: ["意味A"] -> ["意味A", "意味A"]
            result[w.id] = (random.sample(others, len(others)) + others * 2)[:2]
        else:
            # 他の定義が存在しない場合はダミーの選択肢で埋める（2つ）
            result[w.id] = ["(選択肢)", "(選択肢)"]
    return result

@main.route('/get-words', methods=['POST'])
def get_all_words():
    data = request.get_json()
    dict_id = data.get("dict_id")
    words = Word.query.filter(Word.dictionary_id == dict_id).all()
    word_list = [word.to_dict() for word in words]
    return jsonify(word_list)

#; DB全削除(開発用)
@main.route('/delete-db')
def delete_db():
    db.drop_all()
    db.create_all()
    return redirect(url_for('main.index'))