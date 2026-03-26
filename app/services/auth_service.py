from __future__ import annotations

from typing import Literal

from .. import db
from ..models import User

ChangeUsernameResult = Literal["ok", "guest", "empty", "taken"]
ChangePasswordResult = Literal[
    "ok", "guest", "bad_current", "empty_new", "mismatch"
]


def get_or_create_guest_user() -> User:
    guest = User.query.filter_by(username="guest").first()
    if not guest:
        guest = User()
        guest.username = "guest"
        guest.set_password("guest")
        guest.is_guest = True
        db.session.add(guest)
        db.session.commit()
    return guest


def register_new_user(username: str, password: str) -> User:
    user = User()
    user.username = username
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def try_change_username(user: User, new_username: str) -> ChangeUsernameResult:
    if user.is_guest:
        return "guest"
    name = (new_username or "").strip()
    if not name:
        return "empty"
    existing = User.query.filter_by(username=name).first()
    if existing and existing.id != user.id:
        return "taken"
    user.username = name
    db.session.commit()
    return "ok"


def try_change_password(
    user: User, current_password: str, new_password: str, new_password_confirm: str
) -> ChangePasswordResult:
    if user.is_guest:
        return "guest"
    if not user.check_password(current_password):
        return "bad_current"
    if not new_password:
        return "empty_new"
    if new_password != new_password_confirm:
        return "mismatch"
    user.set_password(new_password)
    db.session.commit()
    return "ok"
