from functools import wraps

import requests
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from spotipy.exceptions import SpotifyException, SpotifyOauthError

from soundwavedatabase import add_user, checklogin, getuser
from spotify_service import create_oauth

auth = Blueprint("auth", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("userid"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def _spotify_oauth():
    return create_oauth(
        session,
        current_app.config["SPOTIFY_CLIENT_ID"],
        current_app.config["SPOTIFY_CLIENT_SECRET"],
        current_app.config["SPOTIFY_REDIRECT_URI"],
        current_app.config["SPOTIFY_SCOPE"],
    )


@auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        userid = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if checklogin(userid, password):
            session.clear()
            session["userid"] = userid
            return redirect(url_for("social.conversations"))

        return render_template("login.html", error="Incorrect username or password")

    return render_template("login.html", error=None)


@auth.route("/createaccount", methods=["GET", "POST"])
def createaccount():
    if request.method == "POST":
        userid = (request.form.get("username") or "").strip()
        password1 = request.form.get("password1") or ""
        password2 = request.form.get("password2") or ""

        if not userid or not password1 or not password2:
            return render_template("createaccount.html", error="Please complete all fields")
        if password1 != password2:
            return render_template("createaccount.html", error="Passwords do not match")
        if getuser(userid):
            return render_template("createaccount.html", error="Username already exists")
        if not add_user(userid, password1):
            return render_template("createaccount.html", error="Unable to create account")
        return redirect(url_for("auth.login"))

    return render_template("createaccount.html", error=None)


@auth.route("/verify")
@login_required
def verify():
    if not current_app.config["SPOTIFY_ENABLED"]:
        return redirect(url_for("social.conversations"))

    oauth = _spotify_oauth()
    token = oauth.get_cached_token()
    if not token or not oauth.validate_token(token):
        return redirect(oauth.get_authorize_url())
    return redirect(url_for("social.conversations"))


@auth.route("/callback")
@login_required
def callback():
    if not current_app.config["SPOTIFY_ENABLED"]:
        return redirect(url_for("social.conversations"))

    code = request.args.get("code")
    if not code:
        return redirect(url_for("social.conversations", spotify_error="authorization"))

    try:
        _spotify_oauth().get_access_token(code)
    except (SpotifyException, SpotifyOauthError, requests.RequestException):
        current_app.logger.exception("Spotify authorization failed")
        return redirect(url_for("social.conversations", spotify_error="authorization"))

    return redirect(url_for("social.conversations"))


@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
