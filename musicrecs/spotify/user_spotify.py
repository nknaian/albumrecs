import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from flask import session

from .music import Album
from musicrecs.user import User
from musicrecs.exceptions import SpotifyUserError


SCOPE = 'user-read-currently-playing playlist-modify-private'


def session_cache_path():
    return 'spotify/.caches/' + session.get('uuid')


class SpotifyUser(User):
    def __init__(self):
        super().__init__()

    def check_user_auth(self):
        """Create an spotify auth_manager and check whether the current user has
        a token (has been authorized already).
        
        Return a tuple, where the first value is a boolean representing whether
        or not the user has already authenticated, and the second value is the
        auth_manager.
        """
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SCOPE,
                                                   cache_path=session_cache_path(), 
                                                   show_dialog=True)

        if auth_manager.get_cached_token():
            return (True, auth_manager)
        else:
            return (False, auth_manager)


    def auth_new_user(self, code):
        """Give user an access token to authenticate them"""
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SCOPE,
                                                   cache_path=session_cache_path(), 
                                                   show_dialog=True)
        auth_manager.get_access_token(code)


    def get_current_track(self, auth_manager):
        """Return the current user's track, using the passed in
        auth_manager.
        """
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        track = spotify.current_user_playing_track()
        if not track is None:
            return track
        return "No track currently playing."


    def sp_logout(self):
        os.remove(session_cache_path())
        session.clear()
