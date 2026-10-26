import logging

import requests
from spotipy import Spotify
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.exceptions import SpotifyException, SpotifyOauthError
from spotipy.oauth2 import SpotifyOAuth

from soundwavedatabase import add_curr, add_music, add_song, clear_music, clear_song

logger = logging.getLogger(__name__)


def create_oauth(session, client_id, client_secret, redirect_url, scope):
    return SpotifyOAuth(
        client_id,
        client_secret,
        redirect_uri=redirect_url,
        scope=scope,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )


def create_client(oauth):
    return Spotify(auth_manager=oauth)


def sync_user_music(spotify, userid):
    errors = []

    try:
        recently_played = spotify.current_user_recently_played()
        items = recently_played.get("items", []) if recently_played else []
        if items:
            track = items[0].get("track") or {}
            if track.get("name"):
                add_curr(track["name"], userid)
    except (SpotifyException, SpotifyOauthError, requests.RequestException):
        logger.exception("Failed to sync recently played tracks for %s", userid)
        errors.append("recently played tracks")

    try:
        response = spotify.current_user_top_artists(limit=3)
        items = response.get("items", []) if response else []
        if items:
            artists = []
            for artist in items[:3]:
                name = artist.get("name")
                link = artist.get("external_urls", {}).get("spotify")
                images = artist.get("images") or []
                image = images[0].get("url") if images else None
                if name and link and image:
                    artists.append((name, link, image))

            clear_music(userid)
            for artist in artists:
                add_music(userid, *artist)
    except (SpotifyException, SpotifyOauthError, requests.RequestException):
        logger.exception("Failed to sync top artists for %s", userid)
        errors.append("top artists")

    try:
        response = spotify.current_user_top_tracks(
            limit=5,
            offset=0,
            time_range="short_term",
        )
        items = response.get("items", []) if response else []
        if items:
            songs = []
            for item in items[:5]:
                name = item.get("name")
                artists = item.get("artists") or []
                artist = artists[0].get("name") if artists else None
                if name and artist:
                    songs.append((name, artist))

            clear_song(userid)
            for name, artist in songs:
                add_song(userid, name, artist, "top")
    except (SpotifyException, SpotifyOauthError, requests.RequestException):
        logger.exception("Failed to sync top tracks for %s", userid)
        errors.append("top tracks")

    return errors
