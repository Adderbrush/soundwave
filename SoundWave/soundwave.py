redirect_url = "http://127.0.0.1:8000/callback"
scope = "user-top-read user-read-recently-played user-read-currently-playing"
#defines spotify information
from flask import Flask, request, render_template, redirect, url_for, session, make_response
from flask_socketio import SocketIO, join_room, leave_room, send, emit, rooms
from soundwavedatabase import getuser, add_conversation,checklogin, get_conversations, get_messages, get_conversationid, add_message, add_music, get_music, clear_music, add_curr, get_curr, add_song, get_song, clear_song, add_user, purge, init
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import os
from dotenv import load_dotenv
load_dotenv()
#imports any modules needed
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)
cacheHandler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri=redirect_url, scope=scope, cache_handler=cacheHandler, show_dialog=True)
sp = Spotify(auth_manager=sp_oauth)
#initialises flask and spotify authorisation

@app.route('/', methods=["GET", "POST"])
def login():
    init()
    if request.method == 'POST':
        #this section is ran if data is being sent from the website
        userid = request.form['username'] 
        password = request.form['password']
        #pulls the information from the login request form
        if userid == "purge" and password == "purge":
            purge()
        login = checklogin(userid, password)
        if login == True:
            session['userid'] = userid
            #saves the userid in the session cookies
            return(redirect(url_for('verify'))) 
        #checks the login using a SQLite subroutine, and redirects if login correct 
        else:
            return render_template('login.html', error="Error: Incorrect Username or Password")
        #otherwise redirects to current page
    return render_template('login.html', error=None)


@app.route("/verify")
def verify():
    if not sp_oauth.validate_token(cacheHandler.get_cached_token()):
            #calls this section if there is no spotipy token cashed
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)
            #redirects to spotify login page
    else:
        return redirect(url_for("conversations"))
        #redirects to conversations page if token is cashed


@app.route("/callback")
def callback():
    #this is the url for the spotify redirect
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for("conversations"))
    #Access the cached token and then redirects to conversations

@app.route("/add", methods=["GET", "POST"])
def add():
    ppt1 = session.get('userid')
    if request.method == "POST":
        userid = request.form.get("username")
        x = getuser(userid)
        #checks if user that is attempting to be added exists
        if userid == ppt1:
            return render_template("add.html", error="Error: Cannot Add Yourself")
        elif x == True:
            add_conversation(ppt1, userid)
            return redirect(url_for("conversations"))
            #if it does exist, add conversation and redirect
        else:
            return render_template("add.html", error="Error: No User Found")
            #if not, redirects with an error message
    return render_template("add.html", error=None)

@app.route('/conversations', methods=["GET", "POST"])
def conversations():
    ppt1 = session.get('userid')
    contacts = get_conversations((ppt1,))
    curr = sp.current_user_recently_played()
    #accesses "recently played" spotify data
    print(curr)
    curr = curr["items"]
    curr = curr [0]["track"]["name"]
    add_curr(curr, ppt1)
    #parses through data and saves relevent pieces to database
    data = []
    for i in contacts:
        data.append(get_curr(i))
    for i in range (0,3):
        if i == 0:
            clear_music(ppt1)
        top = sp.current_user_top_artists()
        #accesses "top artists" spotify data
        top = top["items"][i]
        artist = top['name']
        link = top['external_urls']['spotify']
        image = top["images"][0]["url"] 
        add_music(ppt1, artist, link, image)
        #parses through data and saves relevent pieces to database
        length=len(contacts)
    results = sp.current_user_top_tracks(limit=5,offset=0,time_range='short_term')
    #accesses "top tracks" spotify data for short term
    if results["items"] == []:
            print("empty")
    else:
        clear_song(ppt1)
        for i in range(0,5):
            i = results["items"][i]
            name = i['name']
            artist = i["artists"][0]["name"]
            add_song(ppt1, name, artist, "top")
            #parses through data and saves relevent pieces to database
    print(data)
    return render_template("conversations.html", contacts=contacts, data=data, length=length)

@socketio.on('join_chat')
#called by the "join_chat" emit statement
def join_chat(key):
    join_room(key)
    return key
    #uses the "join_room" function from the socket_io libraries


@socketio.on('chat')
#called by "chat" emit statement
def chat(message):
    ppt1 = session.get('userid')
    if len(message["chat"]) != 0:
        #checks that the length of the message isn't zero
        emit('new_chat', (message["chat"]), to=message["key"])
        add_message(message["key"], ppt1, message["chat"])
        #emits a "new_chat" statement that will refresh webpage and adds message to database

@app.route('/conversation/<ppt2>', methods=["GET","POST"])
#dynamic url with ppt2's name after the slash
def conversation(ppt2):
    verify()
    ppt1 = session.get('userid')
    conversationid = get_conversationid(ppt1, ppt2)
    conversationid = conversationid[0]
    session['conversationid'] = conversationid
    messages = get_messages(ppt1, ppt2) 
    #accesses conversationid, messages, ppt1, and ppt2 from url or cookies
    return render_template("chat.html", messages=messages, user=ppt1, id=conversationid, ppt2=ppt2)
    #sends the information to the HTML page

@app.route('/profile/<ppt2>')
def profile(ppt2):
    ppt1 = session.get('userid')
    music = get_music(ppt2)
    top = get_song(ppt2, "top")
    #gets the music data saved in the datebase
    print(top)
    return render_template("profile.html", music=music, ppt2=ppt2, top=top)
    #sends this data to the HTML page

@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    userid = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")
    #pulls the information from the entry boxes
    if request.method == "POST":
        if password1 != password2:
            return render_template("createaccount.html", error="Passwords do not match")
        elif password1 == password2:
            add_user(userid, password1, None)
            return redirect(url_for("login"))
        #verifies if the passwords match, and if they do add the user to the database
    return render_template("createaccount.html", error=None)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)
    init()
    #runs the socketio app and ititalises the database

    #app.run(host='0.0.0.0', port=8000, debug=True)