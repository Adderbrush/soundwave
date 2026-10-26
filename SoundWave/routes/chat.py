from flask import Blueprint, current_app, redirect, render_template, session, url_for
from flask_socketio import emit, join_room

from soundwavedatabase import (
    add_message,
    can_access_conversation,
    get_conversationid,
    get_messages,
)
from .auth import login_required

chat = Blueprint("chat", __name__)


@chat.route("/conversation/<ppt2>")
@login_required
def conversation(ppt2):
    userid = session["userid"]
    conversationid = get_conversationid(userid, ppt2)
    if conversationid is None:
        return redirect(url_for("social.conversations"))

    return render_template(
        "chat.html",
        messages=get_messages(userid, ppt2),
        user=userid,
        id=conversationid[0],
        ppt2=ppt2,
    )


def register_socket_handlers(socketio):
    @socketio.on("join_chat")
    def join_chat(conversationid):
        userid = session.get("userid")
        try:
            conversationid = int(conversationid)
        except (TypeError, ValueError):
            return False

        if not userid or not can_access_conversation(userid, conversationid):
            return False

        join_room(str(conversationid))
        return conversationid

    @socketio.on("chat")
    def send_chat(message):
        userid = session.get("userid")
        if not userid or not isinstance(message, dict):
            return {"ok": False}

        chat_text = (message.get("chat") or "").strip()
        try:
            conversationid = int(message.get("key"))
        except (TypeError, ValueError):
            return {"ok": False}

        if (
            not chat_text
            or len(chat_text) > 2000
            or not can_access_conversation(userid, conversationid)
        ):
            return {"ok": False}

        if not add_message(conversationid, userid, chat_text):
            current_app.logger.error("Could not save message for conversation %s", conversationid)
            return {"ok": False}

        emit(
            "new_chat",
            {"sender": userid, "text": chat_text},
            to=str(conversationid),
        )
        return {"ok": True}
