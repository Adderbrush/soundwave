from .auth import auth
from .chat import chat, register_socket_handlers
from .social import social


def register_routes(app, socketio):
    app.register_blueprint(auth)
    app.register_blueprint(social)
    app.register_blueprint(chat)
    register_socket_handlers(socketio)
