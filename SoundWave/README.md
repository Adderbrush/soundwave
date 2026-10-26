# SoundWave

SoundWave is a social messaging app built with Flask, SQLite and Socket.IO. Create an account, add friends by username, and chat in real time. Spotify is optional; the core app works without Spotify credentials or Spotify Developer Dashboard access.

## Features

- Account registration and login
- One-to-one conversations with persistent, live-updating messages
- Friend discovery by username
- User profiles with optional Spotify listening summaries
- Responsive layouts and empty states

## Run locally

Requirements: Python 3.11 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python soundwave.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), create an account, and add another user to start chatting. The SQLite database is created as `soundwave.db` in the project directory. On startup, SoundWave applies versioned schema migrations that preserve valid existing records, enforce conversation/message/music relationships, and add message timestamps. Invalid legacy test rows are logged and excluded.

## Configuration

The app runs without a `.env` file. For deployments, set a stable `SECRET_KEY` so sessions remain valid across restarts. You can also configure `HOST` and `PORT`.

Spotify features are optional. To enable them, set `CLIENT_ID` and `CLIENT_SECRET` from a Spotify Developer application. `SPOTIFY_REDIRECT_URI` is optional and defaults to `http://127.0.0.1:8000/callback`. Spotify Development Mode may restrict which Spotify accounts can connect; this does not restrict core SoundWave accounts, conversations, or chat.

Keep credentials out of source control. Put local values in an untracked `.env` file or supply them through the deployment environment.

## Project structure

- `soundwave.py` — application factory and extension setup
- `routes/auth.py` — registration, login, logout and optional Spotify authorization
- `routes/social.py` — contacts, conversations dashboard and profiles
- `routes/chat.py` — conversation view and Socket.IO events
- `soundwavedatabase.py` — SQLite access and schema initialization
- `spotify_service.py` — optional Spotify OAuth and music synchronization
- `templates/` and `static/` — HTML templates, styles and assets

For the detailed feature overview, see [`templates/README.md`](templates/README.md).
