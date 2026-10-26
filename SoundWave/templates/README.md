# SoundWave

SoundWave is a social messaging platform built with Python, Flask, SQLite and Socket.IO. Spotify integration is optional: account creation, conversations, profiles and chat work without Spotify credentials or access to a Spotify Developer Dashboard.

## Features

- User registration and session-based login
- One-to-one conversations and persistent real-time chat that updates without page reloads
- Profiles with optional Spotify listening data
- Friend/contact discovery by username
- Responsive empty states when music data is unavailable

## Run without Spotify

1. Install dependencies with `pip install -r requirements.txt`.
2. Run `python soundwave.py`.
3. Open `http://127.0.0.1:8000`, create an account and start chatting.

No `.env` file or Spotify credentials are required for the core features. Set a stable `SECRET_KEY` for deployments; the generated local/demo key changes between restarts, which invalidates sessions.

## Optional Spotify integration

Set `CLIENT_ID` and `CLIENT_SECRET` in environment variables or a local `.env` file to enable Spotify OAuth and music summaries. `SPOTIFY_REDIRECT_URI` is optional and defaults to `http://127.0.0.1:8000/callback`.

Spotify Development Mode can restrict which Spotify accounts may authorize the app. That restriction affects only music integration; it does not prevent users from registering, viewing profiles, adding contacts or chatting.

The application uses SQLite in `soundwave.db` and stores account, conversation, message and optional music data locally.

## Technologies

- Python, Flask, Flask-SocketIO and Jinja2
- SQLite
- Spotipy and the Spotify Web API (optional feature)
- HTML and CSS

## Project structure

- `soundwave.py` — application factory and extension configuration
- `routes/auth.py` — account, login, logout and optional Spotify authorization
- `routes/social.py` — contacts, dashboard and profiles
- `routes/chat.py` — conversation view and authenticated Socket.IO handlers
- `soundwavedatabase.py` — SQLite persistence
- `spotify_service.py` — optional Spotify authorization and music synchronization
- `templates/` and `static/` — UI templates, styles and assets
