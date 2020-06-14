# gTagger

A CLI for automatically meta-tagging music files using [Genius' API](https://genius.com/developers).

## Features
- Infers song title from filename and uses it to match with Genius' database
- Batch-mode for operating on multiple files and folders
- Can also take a custom Genius' URL
- Can also take a custom query for matching
- Works in CLI and can be imported into Python

## Installation
- Install using `pip install git+https://github.com/Haroon96/gTagger`
- [Signup on Genius](https://genius.com/developers) to get an API token
- Run the program and enter the token when prompted

## CLI usage
```
gtagger [-h] [--query QUERY] [--genius-url GENIUS_URL]
           sources [sources ...]

positional arguments:
sources               source file(s) or folder(s)

optional arguments:
-h, --help            show this help message and exit
--query QUERY         Query suffix (use if filename alone isn't sufficient
                    for inferring song title)
--genius-url GENIUS_URL
                    Genius.com URL to use for tagging (use if program
                    fails to find it itself)

```

### Examples
- To tag all files in your music directory
  - `gtagger ~/Music`
- To tag a file with a specific Genius URL
  - `gtagger song.mp3 --genius-url https://genius.com/...`
- To improve matching if the filename is vague, use the `query` parameter to attach a a more specific identifier
  - Attach artist name so the matching becomes more specific
    - `gtagger "Face to Face.mp3" --query "Daft Punk"`
  - Attach album name when working on that album's folder
    - `gtagger "~/Music/Daft Punk" --query "Random Access Memories"`
- Batch-mode
  - `gtagger ~/Music song1.mp3 song2.mp3`

## Python module usage
### Example
```
import os
from gtagger import gTagger

# your Genius API token
token = '...'

# path containing music
source = '~/Music'

# instantiate the tagger by providing
# token and an optional logger
gt = gTagger(token, print)

for filename in os.listdir(source):
    path = os.path.join(source, filename)

    # tag the file by providing
    # a query (filename) for matching
    # and the path to the file
    gt.tag(filename, path)
    
    # additionally the tag method also takes a genius_url
    # parameter for directly tagging instead of inferring from filename
```
