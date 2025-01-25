import spotipy

SPOTIPY_CLIENT_ID = "d64cddc01d3948a293335bd38598056a"
SPOTIPY_CLIENT_SECRET = "828eba458e50416893b17e1f5b0e0954"
SPOTIPY_REDIRECT_URI = "https://example.com/"

scope = "user-modify-playback-state"
client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET) 
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                                              redirect_uri=SPOTIPY_REDIRECT_URI,
                                                              scope=scope)) 

print(sp.current_playback())