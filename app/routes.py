from typing import cast

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import Dictionary, User
from .form import LoginForm, RegistrationForm
from . import login_manager
from .services import auth_service
from .services import dictionary_service
from .services import shelf_service
from .services import quiz_service
from .services import dashbard_service

main = Blueprint("main", __name__)


def require_not_guest():
    if current_user.is_authenticated and current_user.is_guest:
        abort(403)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("ログインしました")
            return redirect(url_for("main.index"))
        flash("ユーザー名またはパスワードが間違っています")
    return render_template("login.html", form=form)


@main.route("/guest-login", methods=["GET", "POST"])
def guest_login():
    guest = auth_service.get_or_create_guest_user()
    login_user(guest)
    flash("ゲストユーザーとしてログインしました")
    return redirect(url_for("main.index"))


@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = (form.username.data or "").strip()
        password = form.password.data or ""
        auth_service.register_new_user(username, password)
        flash("登録が完了しました")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main.route("/logout")
def logout():
    logout_user()
    flash("ログアウトしました")
    return redirect(url_for("main.login"))


@main.route("/change-username", methods=["POST"])
@login_required
def change_username():
    result = auth_service.try_change_username(
        cast(User, current_user), request.form.get("new_username", "")
    )
    if result == "guest":
        flash("ゲストユーザーは変更できません")
    elif result == "empty":
        flash("ユーザー名を入力してください")
    elif result == "taken":
        flash("そのユーザー名は既に使用されています")
    else:
        flash("ユーザー名を変更しました")
    return redirect(request.referrer or url_for("main.index"))


@main.route("/change-password", methods=["POST"])
@login_required
def change_password():
    result = auth_service.try_change_password(
        cast(User, current_user),
        request.form.get("current_password", ""),
        request.form.get("new_password", ""),
        request.form.get("new_password_confirm", ""),
    )
    if result == "guest":
        flash("ゲストユーザーは変更できません")
    elif result == "bad_current":
        flash("現在のパスワードが正しくありません")
    elif result == "empty_new":
        flash("新しいパスワードを入力してください")
    elif result == "mismatch":
        flash("新しいパスワードが一致しません")
    else:
        flash("パスワードを変更しました")
    return redirect(request.referrer or url_for("main.index"))


@main.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    ctx = dashbard_service.build_menu_page_context(current_user.id)
    return render_template("menu.html", **ctx)

def check_is_creator_user(dictionary_id: int) -> bool:
    require_not_guest()
    dictionary = Dictionary.query.get_or_404(dictionary_id)
    if dictionary.creator_user_id != current_user.id:
        flash("作成者以外は編集できません")
        return False
    return True

@main.route("/create-dictionary", methods=["GET", "POST"])
def create_dictionary():
    require_not_guest()
    cover_colors = ["#773333", "#334477", "#335544", "#333333", "#C56700"]

    if request.method == "POST":
        title = request.form.get("cover-title", "").strip()
        cover_color = request.form.get("cover-color", "")
        creator_user_id = current_user.id
        is_private = request.form.get("is_private", "false") == "true"

        if not title:
            return render_template(
                "create_dictionary.html",
                cover_colors=cover_colors,
                error="辞書名を入力してください",
            )

        new_dictionary = dictionary_service.create_dictionary(title, cover_color, creator_user_id, is_private)
        return redirect(
            url_for("main.add_words", dictionary_id=new_dictionary.id, page=0)
        )

    return render_template("create_dictionary.html", cover_colors=cover_colors)


@main.route("/update-dictionary/<int:dictionary_id>", methods=["GET", "POST"])
def update_dictionary(dictionary_id):
    require_not_guest()
    if not check_is_creator_user(dictionary_id):
        return redirect(url_for("main.view_words", dictionary_id=dictionary_id, page=0))
    cover_colors = ["#773333", "#334477", "#335544", "#333333", "#C56700"]
    dictionary = Dictionary.query.get_or_404(dictionary_id)
    original_title = dictionary.title
    original_color = dictionary.cover_color
    original_is_private = dictionary.is_private

    if request.method == "POST":
        new_title = request.form.get("cover-title", "").strip()
        new_color = request.form.get("cover-color", "")
        new_is_private = request.form.get("is_private", "false") == "true"

        if not new_title:
            return render_template(
                "dictionary_detail.html",
                dictionary=dictionary,
                cover_colors=cover_colors,
                error="辞書名を入力してください",
            )

        if original_title != new_title or original_color != new_color or original_is_private != new_is_private:
            dictionary_service.update_dictionary_metadata(dictionary, new_title, new_color, new_is_private)
            return redirect(url_for("main.update_dictionary", dictionary_id=dictionary.id))

    return render_template(
        "dictionary_detail.html", dictionary=dictionary, cover_colors=cover_colors
    )


@main.route("/delete-dictionary/<int:dictionary_id>", methods=["POST"])
def delete_dictionary(dictionary_id):
    require_not_guest()
    if not check_is_creator_user(dictionary_id):
        return redirect(url_for("main.view_words", dictionary_id=dictionary_id, page=0))
    dictionary = Dictionary.query.get_or_404(dictionary_id)
    dictionary_service.delete_dictionary_by_id(dictionary)
    return redirect(url_for("main.dictionary_shelf"))


@main.route("/add-words/<int:dictionary_id>/<int:page>")
def add_words(dictionary_id, page):
    require_not_guest()
    if not check_is_creator_user(dictionary_id):
        return redirect(url_for("main.view_words", dictionary_id=dictionary_id, page=page))
    ctx = dictionary_service.build_add_words_page_context(dictionary_id, page)
    if not ctx:
        return redirect(url_for("main.index"))
    return render_template("add_words.html", **ctx)


@main.route("/view-words/<int:dictionary_id>/<int:page>")
def view_words(dictionary_id, page):
    ctx = dictionary_service.build_view_words_page_context(dictionary_id, page)
    if not ctx:
        return redirect(url_for("main.index"))
    return render_template("view_words.html", **ctx)


@main.route("/add-words/<int:dictionary_id>/save-words", methods=["POST"])
def save_words(dictionary_id):
    require_not_guest()
    if not check_is_creator_user(dictionary_id):
        return jsonify({"success": False, "error": "作成者以外は編集できません"}), 403
    data = request.get_json() or {}
    words = data.get("words") or []
    page_index = data.get("page_index", 0)

    ok, err, payload = dictionary_service.save_words_bulk(
        dictionary_id, page_index, words
    )
    if not ok:
        return jsonify({"success": False, "error": err}), 404
    return jsonify(payload)


@main.route("/add-words/<int:dictionary_id>/delete-word/<int:word_id>", methods=["POST"])
def delete_word(dictionary_id, word_id):
    require_not_guest()
    if not check_is_creator_user(dictionary_id):
        return jsonify({"success": False, "error": "作成者以外は編集できません"}), 403
    ok, err = dictionary_service.delete_word_in_dictionary(dictionary_id, word_id)
    if not ok:
        return jsonify({"success": False, "error": err}), 404
    return jsonify({"success": True})


@main.route("/dictionary-shelf/favorite/<int:dictionary_id>", methods=["POST"])
def toggle_favorite(dictionary_id):
    data = request.get_json(silent=True) or {}
    ok, err, is_favorite = dictionary_service.toggle_dictionary_favorite(
        dictionary_id, data
    )
    if not ok:
        return jsonify({"success": False, "error": err}), 404
    return jsonify({"success": True, "is_favorite": is_favorite})


@main.route("/dictionary-shelf")
def dictionary_shelf():
    user_id = current_user.id if current_user.is_authenticated else None
    ctx = shelf_service.build_dictionary_shelf_context(request.args, user_id)
    return render_template("dictionary_shelf.html", **ctx)


@main.route("/quiz-menu")
def quiz_menu():
    # public は全員、private は作成者本人のみ表示
    user_id = None
    if current_user.is_authenticated and not current_user.is_guest:
        user_id = current_user.id
    dictionaries = dictionary_service.visible_dictionaries_query(user_id).order_by(Dictionary.id).all()
    return render_template("quiz_menu.html", dictionaries=dictionaries)


@main.route("/quiz-play/<dict_id>/<int:quiz_type>")
def quiz_play(dict_id, quiz_type):
    dictionary = Dictionary.query.get_or_404(dict_id)
    words = dictionary_service.list_words_for_dict(dict_id)
    dict_name = dictionary.title

    if quiz_type == 1:
        quiz_data = quiz_service.build_choice_quiz_data(words)
        return render_template(
            "quiz_play_choice.html",
            quiz_data=quiz_data,
            dict_id=dict_id,
            dict_name=dict_name,
            quiz_type=quiz_type,
        )
    if quiz_type == 2:
        return render_template(
            "quiz_play_description.html",
            dict_id=dict_id,
            quiz_type=quiz_type,
            dict_name=dict_name,
            dictionary=dictionary,
        )
    return redirect(url_for("main.quiz_menu"))


@main.route("/get-words", methods=["POST"])
def get_all_words():
    data = request.get_json()
    dict_id = data.get("dict_id")
    words = dictionary_service.list_words_for_dict(dict_id)
    word_list = [word.to_dict() for word in words]
    return jsonify(word_list)


@main.route("/delete-db")
def delete_db():
    db.drop_all()
    db.create_all()
    return redirect(url_for("main.index"))
