import sys
import os
import re
import json
import requests
import unicodedata
from bs4 import BeautifulSoup
from googlesearch import search as gsearch
from mutagen import File
from mutagen.id3 import TIT2, TPE1, TALB, TPE2, USLT, APIC, TCON, TRCK
from pathvalidate import sanitize_filename

class gTagger:

    def __init__(self, token, log=lambda *x : None):
        self.token = token
        self.log = log

    # fetches a genius page and extracts song_id
    def __fetch_page(self, url):
        # fetch page
        r = requests.get(url, headers={'User-Agent':'haroon96/gTagger'})
        html = r.text

        # get song_id
        key = re.search(r'(?i)"song ?id.?":([0-9]+)', html)

        # if key is None, there was an issue in the call - try again
        if key is None:
            raise Exception('No Song ID in this URL!')

        # extract song_id
        song_id = key.group(1)

        return song_id, html

    # gets in
    def __get_genius_data(self, query, genius_url):

        # get top google result is no genius_url provided
        urls = gsearch(f'site:genius.com {query} lyrics', stop=5) if genius_url is None else [genius_url]

        for url in urls:
            self.log("\tTrying URL", url)

            try:
                song_id, html = self.__fetch_page(url)

                # replace all <br> with new-lines
                html = re.sub(r'<br/?>', '\n', html)
                
                # try to get lyrics
                soup = BeautifulSoup(html, 'html.parser')

                try:
                    lyrics = None
                    l = re.compile(r'(?i)^lyrics')
                    lyrics = soup.find('div', attrs={'class': l}).text.strip()
                except:
                    self.log("\tFailed to fetch lyrics!")

                return (song_id, lyrics)
            except Exception as e:
                self.log(f'\t{e}')

        raise Exception('\tFailed to find the song on Genius.com!')
            
    def __get_track_number(self, album_url, song_url):
        r = requests.get(album_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        tracks = soup.find_all('div', attrs={'class': 'chart_row'})
        track_number = [i for i in tracks if song_url in str(i)][0]
        return int(track_number.text.split()[0])

    def __get_song_metadata(self, q, genius_url):
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # search for song on genius.com
        # lyrics aren't available in genius API, scrape them directly
        song_id, lyrics = self.__get_genius_data(q, genius_url)

        # fetch song metadata using genius.com API
        r = requests.get(f'https://api.genius.com/songs/{song_id}', headers=headers)

        # parse response and return music info
        js = r.json()['response']['song']
        js['lyrics'] = lyrics

        if js['album'] is not None:
            js['track_number'] = self.__get_track_number(js['album']['url'], js['url'])
        else:
            js['track_number'] = None

        return js

    # return album art url or song url if single
    def __get_cover_art_url(self, music_info):
        if music_info['album'] is not None:
            return music_info['album']['cover_art_url']
        return music_info['song_art_image_url']

    # return album name or suffix 'Single' if the song is a single
    def __get_album_info(self, music_info):
        if music_info['album'] is not None:
            return (music_info['album']['name'], music_info['album']['artist']['name'])
        return (f"{music_info['title']} - Single", music_info['primary_artist']['name'])

    # return a normalized title for the song
    def __get_title(self, music_info):
        title = music_info['title_with_featured'].replace('Ft.', 'feat.')
        return unicodedata.normalize('NFKD', title)

    # rename the file appropriately
    def __rename_file(self, title, artist, oldfilepath):
        basepath, oldname = os.path.split(oldfilepath)
        _, ext = os.path.splitext(oldname)
        # remove special chars
        newname = sanitize_filename(f'{artist} - {title}{ext}')
        # remove extra whitespaces
        newname = re.sub(r'\s+', ' ', newname)
        newfilepath = os.path.join(basepath, newname)
        os.rename(oldfilepath, newfilepath)
        return newfilepath

    def __embed_metatags(self, query, filename, genius_url):

        # search for song metadata
        music_info = self.__get_song_metadata(query, genius_url)

        # embed relevant tags using mutagen
        audio_file = File(filename)

        # embed title and artist info
        title = self.__get_title(music_info)
        artist = music_info['primary_artist']['name']
        audio_file['TIT2'] = TIT2(encoding=3, text=[title])
        audio_file['TPE1'] = TPE1(encoding=3, text=[artist])

        # embed album info
        album_name, album_artist = self.__get_album_info(music_info)
        audio_file['TALB'] = TALB(encoding=3, text=[album_name])
        audio_file['TPE2'] = TPE2(encoding=3, text=[album_artist])
        
        # embed other tags
        audio_file['USLT::XXX'] = USLT(encoding=1, lang='XXX', desc='', text=music_info['lyrics'])
        audio_file['TRCK'] = TRCK(encoding=3, text=[music_info['track_number']])

        try:
            artwork = requests.get(self.__get_cover_art_url(music_info), stream=True)
            audio_file['APIC:'] = APIC(encoding=3, mime="image/jpeg", type=3, desc='', data=artwork.raw.read())
        except Exception as e:
            self.log(f"\tFailed to embed artwork for title: {title}", e)

        # save the new file
        audio_file.save()

        # return new title and filename
        return f'{artist} - {title}', self.__rename_file(title, artist, filename)

    def tag(self, query, filename, genius_url=None):

        try:
            return self.__embed_metatags(query, filename, genius_url)
        except Exception as e:
            self.log(e)

        return query, filename