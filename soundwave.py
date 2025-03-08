CLIENT_ID = "b12cca34dc264e12bb7f1e57aaab857d"
CLIENT_SECRET = "2cd4bfaf0426483895ad52f812ab2c74"
redirect_url = "http://127.0.0.1:5000/callback"
scope = "user-top-read user-read-recently-played user-read-currently-playing"
from flask import Flask, request, render_template, redirect, url_for, session, make_response
from flask_socketio import SocketIO, join_room, leave_room, send, emit, rooms
from soundwavedatabase import getuser, add_conversation,checklogin, get_conversations, get_messages, get_conversationid, add_message, add_music, get_music, clear_music, add_curr, get_curr, add_song, get_song, clear_song, add_user
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
socketio = SocketIO(app)
cacheHandler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri=redirect_url, scope=scope, cache_handler=cacheHandler, show_dialog=True)


sp = Spotify(auth_manager=sp_oauth)


@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        userid = request.form['username'] 
        password = request.form['password']
        login = checklogin(userid, password)
        if login == True:
            session['userid'] = userid
            return(redirect(url_for('verify')))    
        else:
            return render_template('login.html', error="Error: Incorrect Username or Password")
    return render_template('login.html', error=None)


@app.route("/verify")
def verify():
    if not sp_oauth.validate_token(cacheHandler.get_cached_token()):
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)
    else:
        return redirect(url_for("conversations"))


@app.route("/callback")
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for("conversations"))

@app.route("/add", methods=["GET", "POST"])
def add():
    ppt1 = session.get('userid')
    if request.method == "POST":
        userid = request.form.get("username")
        x = getuser(userid)
        if x == True:
            add_conversation(ppt1, userid)
            return redirect(url_for("conversations"))
        else:
            return render_template("add.html", error="Error: No User Found")
    return render_template("add.html", error=None)

@app.route('/conversations', methods=["GET", "POST"])
def conversations():
    ppt1 = session.get('userid')
    contacts = get_conversations((ppt1,))
    curr = sp.current_user_recently_played()
    print(curr)
    curr = curr["items"]
    curr = curr [0]["track"]["name"]
    add_curr(curr, ppt1)
    data = []
    for i in contacts:
        data.append(get_curr(i))
    for i in range (0,3):
        if i == 0:
            clear_music(ppt1)
        top = sp.current_user_top_artists()
        top = top["items"][i]
        artist = top['name']
        link = top['external_urls']['spotify']
        image = top["images"][0]["url"] 
        add_music(ppt1, artist, link, image)
        length=len(contacts)
    results = sp.current_user_top_tracks(limit=5,offset=0,time_range='short_term')
    if results["items"] == []:
            print("empty")
    else:
        clear_song(ppt1)
        for i in range(0,5):
            i = results["items"][i]
            name = i['name']
            artist = i["artists"][0]["name"]
            add_song(ppt1, name, artist, "top")
    print(data)
    return render_template("conversations.html", contacts=contacts, data=data, length=length)

@socketio.on('join_chat')
def join_chat(key):
    join_room(key)
    return key


@socketio.on('chat')
def chat(message):
    ppt1 = session.get('userid')
    if len(message["chat"]) != 0:
        emit('new_chat', (message["chat"]), to=message["key"])
        add_message(message["key"], ppt1, message["chat"])

@app.route('/conversation/<ppt2>', methods=["GET","POST"])
def conversation(ppt2):
    verify()
    ppt1 = session.get('userid')
    conversationid = get_conversationid(ppt1, ppt2)
    conversationid = conversationid[0]
    session['conversationid'] = conversationid
    messages = get_messages(ppt1, ppt2) 
    return render_template("chat.html", messages=messages, user=ppt1, id=conversationid, ppt2=ppt2)

@app.route('/profile/<ppt2>')
def profile(ppt2):
    ppt1 = session.get('userid')
    music = get_music(ppt2)
    top = get_song(ppt2, "top")
    print(top)
    return render_template("profile.html", music=music, ppt2=ppt2, top=top)

@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    userid = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")
    if request.method == "POST":
        if password1 != password2:
            return render_template("createaccount.html", error="Passwords do not match")
        elif password1 == password2:
            add_user(userid, password1)
            return redirect(url_for("login"))
    return render_template("createaccount.html", error=None)

if __name__ == "__main__":

    app.run(port=8000, debug=True, allow_unsafe_werkzeug=True)
