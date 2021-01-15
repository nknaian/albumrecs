import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .music import Album

class UserSpotify:
    def __init__(self, auth_manager):
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_latest_album(self):
        results = self.sp.current_user_saved_albums(limit=1)

        album_items = results['items']

        return Album(album_items[0]['album'])
