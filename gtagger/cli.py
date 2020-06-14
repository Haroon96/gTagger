import os
from sys import platform as plt
from argparse import ArgumentParser
from .gtagger import gTagger

def parse_args():
    parser = ArgumentParser(description='Tag metadata into song files')
    parser.add_argument('sources', type=str, nargs='+', help='source file(s) or folder(s)')
    parser.add_argument('--query', type=str, help='Query suffix (use if filename alone isn\'t sufficient for inferring song title)')
    parser.add_argument('--genius-url', type=str, help='Genius.com URL to use for tagging (use if program fails to find it itself)')
    return parser.parse_args()

def read_token():
    # identify config folder based on OS
    if "linux" in plt:
        root = os.path.join(os.environ['HOME'], '.gtagger')
    elif "win" in plt:
        root = os.path.join(os.environ['LOCALAPPDATA'], 'gTagger')
    else:
        raise Exception('Unsupported operating system')
    
    # identify token file
    tokenfile = os.path.join(root, 'token')

    # check if token file doesn't exist
    if not os.path.exists(tokenfile):
        # input token from user
        token = input("Genius API token not set! Please enter token: ")
        # if root dir doesn't exist, create it
        if not os.path.exists(root):
            os.makedirs(root)
        # write token to file
        open(tokenfile, 'w').write(token)

    # return token value
    return open(tokenfile).read()

def is_audio(ext):
    return ext in ['.mp3', '.aac', '.wav', '.wma', '.ogg', '.m3u', '.flac']

def cli():
    args = parse_args()
    token = read_token()

    # create a gTagger instance and set logger to print
    gt = gTagger(token, log=print)

    # list of audio files
    files = []

    for src in args.sources:
        # identify as directory or file and proceed accordingly
        _files = [os.path.join(src, i) for i in os.listdir(src)] if os.path.isdir(src) else [src]

        # short-list audio files
        _files = [i for i in _files if is_audio(os.path.splitext(i)[1])]

        # add files to masterlist
        files.extend(_files)

    print(f"\nFound {len(files)} audio file(s)")

    for fp in files:
        # extract title from path
        _, title = os.path.split(fp)
        # extract filename as query
        query, _ = os.path.splitext(title)

        # check if user provided a query fix
        if args.query is not None: 
            query = f'{args.query} {query}'

        try:
            print(f'\nTagging {title}...')
            title, newfile = gt.tag(query, fp, args.genius_url)
            print(f"\tRenaming file to {os.path.basename(newfile)}...")
            print("\tDone!")
        except Exception as e:
            print(f"Failed to tag! {e}")