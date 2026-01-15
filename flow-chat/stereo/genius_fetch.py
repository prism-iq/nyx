#!/usr/bin/env python3
"""
GENIUS LYRICS FETCHER
"""
import requests
import json
import os
from bs4 import BeautifulSoup

class GeniusLyrics:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def search_song(self, query):
        """Cherche une chanson"""
        url = f"{self.base_url}/search"
        params = {"q": query}
        
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_lyrics(self, song_url):
        """Récupère les paroles depuis l'URL Genius"""
        try:
            response = requests.get(song_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Genius utilise des divs avec data-lyrics-container
            lyrics_divs = soup.find_all('div', {'data-lyrics-container': 'true'})
            
            if lyrics_divs:
                lyrics = ""
                for div in lyrics_divs:
                    lyrics += div.get_text(separator='\n')
                return lyrics.strip()
            
            return "Paroles non trouvées"
        except Exception as e:
            return f"Erreur: {str(e)}"
    
    def fetch_full_lyrics(self, artist, song):
        """Recherche et récupère les paroles complètes"""
        query = f"{artist} {song}"
        search_result = self.search_song(query)
        
        if search_result.get('response', {}).get('hits'):
            hit = search_result['response']['hits'][0]
            song_info = hit['result']
            song_url = song_info['url']
            
            print(f"🎵 Trouvé: {song_info['full_title']}")
            print(f"🔗 URL: {song_url}")
            
            lyrics = self.get_lyrics(song_url)
            return {
                'title': song_info['full_title'],
                'url': song_url,
                'lyrics': lyrics
            }
        
        return None

if __name__ == "__main__":
    import sys
    
    token = os.getenv('GENIUS_TOKEN')
    if not token:
        print("❌ GENIUS_TOKEN manquant")
        sys.exit(1)
    
    genius = GeniusLyrics(token)
    
    if len(sys.argv) >= 3:
        artist = sys.argv[1]
        song = " ".join(sys.argv[2:])
        
        result = genius.fetch_full_lyrics(artist, song)
        if result:
            print(f"\n📝 PAROLES: {result['title']}")
            print("=" * 50)
            print(result['lyrics'])
        else:
            print("❌ Aucune parole trouvée")
    else:
        print("Usage: python3 genius_fetch.py 'Artist' 'Song Title'")