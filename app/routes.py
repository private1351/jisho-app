from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from . import db
from .models import Dictionary, Word

main = Blueprint('main', __name__)

MAX_LINES_PER_PAGE = 23

def _reflow_dictionary_words(dictionary_id: int):
    """
    辞書内の全単語を ID順に並べ、左ページ→右ページ→次の見開き…の順で詰め直して
    page_index を振り直す（スクロールせずページ送りするための整形）。
    """
    words = Word.query.filter_by(dictionary_id=dictionary_id).order_by('id').all()
    page_index = 0
    left_lines = 0
    right_lines = 0

    for w in words:
        lines = 1 + (w.line_count or 2)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            w.page_index = page_index
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            w.page_index = page_index
            right_lines += lines
        else:
            page_index += 1
            left_lines = lines
            right_lines = 0
            w.page_index = page_index

    db.session.commit()

@main.route('/')
def index():
    return render_template('menu.html')

@main.route('/create-dictionary', methods=['GET', 'POST'])
def create_dictionary():
    cover_colors = ['#773333', '#334477', '#335544', '#333333']

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
    _reflow_dictionary_words(dictionary_id)

    cover_color = dictionary.cover_color
    words = (Word.query
             .filter_by(dictionary_id=dictionary_id, page_index=page)
             .order_by('id')
             .all())

    left_words = []
    right_words = []

    left_lines = 0
    right_lines = 0

    for word in words:
        lines = 1 + (word.line_count)
        if left_lines + lines <= MAX_LINES_PER_PAGE:
            left_words.append(word)
            left_lines += lines
        elif right_lines + lines <= MAX_LINES_PER_PAGE:
            right_words.append(word)
            right_lines += lines
        else:
            # データが溢れている場合のフォールバック（基本は reflow で発生しない想定）
            right_words.append(word)

    return render_template('add_words.html',
                        dictionary=dictionary,
                        cover_color=cover_color,
                        page=page,
                        left_words=left_words,
                        right_words=right_words)

# 単語の一括保存API（手動保存用）
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

        # 新規は「単語」が空なら保存しない（空行を増やさないため）
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
            new_word = Word(
                word=word_text,
                definition=definition_text,
                dictionary_id=dictionary_id,
                line_count=line_count,
                page_index=page_index
            )
            db.session.add(new_word)
            db.session.flush()  # id確定
            created += 1
            touched_ids.append(new_word.id)

    db.session.commit()

    # 全体を詰め直して「左が埋まったら右→次ページ」の形に整形
    _reflow_dictionary_words(dictionary_id)

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

# 辞書一覧ページ
@main.route('/dictionary-shelf')
def dictionary_shelf():
    dictionaries = Dictionary.query.all()
    return render_template('dictionary_shelf.html', dictionaries=dictionaries)

#; DB全削除(開発用)
@main.route('/delete-db')
def delete_db():
    db.drop_all()
    db.create_all()
    return redirect(url_for('main.index'))