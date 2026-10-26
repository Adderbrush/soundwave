import os
import secrets

from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

from routes import register_routes
from soundwavedatabase import init

load_dotenv()

socketio = SocketIO()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
        SPOTIFY_CLIENT_ID=os.getenv("CLIENT_ID"),
        SPOTIFY_CLIENT_SECRET=os.getenv("CLIENT_SECRET"),
        SPOTIFY_REDIRECT_URI=os.getenv(
            "SPOTIFY_REDIRECT_URI",
            "http://127.0.0.1:8000/callback",
        ),
        SPOTIFY_SCOPE="user-top-read user-read-recently-played",
    )
    app.config["SPOTIFY_ENABLED"] = bool(
        app.config["SPOTIFY_CLIENT_ID"] and app.config["SPOTIFY_CLIENT_SECRET"]
    )
    if test_config:
        app.config.update(test_config)

    socketio.init_app(app)
    register_routes(app, socketio)

    @app.context_processor
    def template_settings():
        return {"spotify_enabled": app.config["SPOTIFY_ENABLED"]}

    return app


app = create_app()


if __name__ == "__main__":
    init()
    socketio.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
