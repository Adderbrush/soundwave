import requests

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from spotipy.exceptions import SpotifyException, SpotifyOauthError

from soundwavedatabase import (
    add_conversation,
    get_conversations,
    get_curr,
    get_music,
    get_song,
    getuser,
)
from spotify_service import create_client, create_oauth, sync_user_music
from .auth import login_required

social = Blueprint("social", __name__)


def _spotify_oauth():
    return create_oauth(
        session,
        current_app.config["SPOTIFY_CLIENT_ID"],
        current_app.config["SPOTIFY_CLIENT_SECRET"],
        current_app.config["SPOTIFY_REDIRECT_URI"],
        current_app.config["SPOTIFY_SCOPE"],
    )


@social.route("/add", methods=["GET", "POST"])
@login_required
def add():
    userid = session["userid"]
    if request.method == "POST":
        contact = (request.form.get("username") or "").strip()
        if not contact:
            return render_template("add.html", error="Please enter a username")
        if contact == userid:
            return render_template("add.html", error="You cannot add yourself")
        if not getuser(contact):
            return render_template("add.html", error="No user found with that username")
        if not add_conversation(userid, contact):
            return render_template("add.html", error="You are already connected to that user")
        return redirect(url_for("social.conversations"))

    return render_template("add.html", error=None)


@social.route("/conversations")
@login_required
def conversations():
    userid = session["userid"]
    contacts = get_conversations(userid)
    data = []

    for contact in contacts:
        current = get_curr(contact)
        data.append(current[0][0] if current and current[0][0] else None)

    spotify_error = request.args.get("spotify_error")
    spotify_connected = False
    if current_app.config["SPOTIFY_ENABLED"]:
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        spotify_connected = bool(token and oauth.validate_token(token))
        if spotify_connected:
            try:
                errors = sync_user_music(create_client(oauth), userid)
                if errors:
                    spotify_error = "sync"
            except (SpotifyException, SpotifyOauthError, requests.RequestException):
                current_app.logger.exception("Could not connect to Spotify for %s", userid)
                spotify_error = "sync"

    return render_template(
        "conversations.html",
        contacts=contacts,
        data=data,
        user=userid,
        spotify_connected=spotify_connected,
        spotify_error=spotify_error,
    )


@social.route("/profile/<ppt2>")
@login_required
def profile(ppt2):
    if not getuser(ppt2):
        return redirect(url_for("social.conversations"))
    return render_template(
        "profile.html",
        music=get_music(ppt2),
        ppt2=ppt2,
        top=get_song(ppt2, "top"),
    )
