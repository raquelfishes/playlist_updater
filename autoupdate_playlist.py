import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import CacheFileHandler
import json
import random

from tqdm import tqdm
from tqdm.auto import trange

## WITH SPOTIPY
def getTrackURIsFromPlaylist(playlistId, urisIds, sp):
    urisIds.clear()
    offset = 0
    while True:
        response = sp.playlist_items(playlistId, offset=offset, fields='items.track.uri,total', additional_types=['track'])
        if len(response['items']) == 0:
            break
        offset += len(response['items'])
        urisIds.extend([item['track']['uri'] for item in response['items'] if item['track'] != None])

def main(log):
    jsonFile = open("./config.json", "r")
    info = json.load(jsonFile)

    credentialsFile = open("./credentials.json", "r")
    spotify_auth_data = json.load(credentialsFile)

    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(open_browser=False, client_id=spotify_auth_data['spotify_client_id'], client_secret=spotify_auth_data['spotify_client_secret'], redirect_uri=spotify_auth_data['spotify_redirect_uri']))
    
    # Authentication for headless server
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(open_browser=False, scope=spotify_auth_data['spotify_scope'], client_id=spotify_auth_data['spotify_client_id'], client_secret=spotify_auth_data['spotify_client_secret'], redirect_uri=spotify_auth_data['spotify_redirect_uri'], cache_handler=CacheFileHandler(username='spotify')))

    ### Add ids to playlis
    for i in trange(len(info['tasks']), desc="Updating...", ncols=100):
        item = info['tasks'][i]
        results = sp.playlist(item['playlistURI'])
        if log:
            tqdm.write("Playlist: " + results['name'])
        pl_to_id = item['playlistURI']
        list_to_clear = []
        getTrackURIsFromPlaylist(pl_to_id, list_to_clear, sp)
        sp.playlist_remove_all_occurrences_of_items(pl_to_id, list_to_clear)
            
        list_to_random = []
        for playlistRef in tqdm(item['references'], desc="Updating...", ascii=False, ncols=100):
            playlistInfo = sp.playlist(playlistRef)
            if log:
                tqdm.write( "Checking playlist: " + playlistInfo['name'])
            auxList = []
            getTrackURIsFromPlaylist(playlistRef, auxList, sp)
            list_to_random.extend(auxList)
            
        # Clear possible dupplicates
        list_to_random = list(set(list_to_random))
        trackCount = min(item['trackCount'], len(list_to_random))
        resultTracks = random.sample(list_to_random, item['trackCount'])
        sp.playlist_add_items(pl_to_id,resultTracks)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create args schema')
    parser.add_argument('--log_info', action=argparse.BooleanOptionalAction, required=False, help='Active print playlist logging info')
    args = parser.parse_args()
    main(log=args.log_info)