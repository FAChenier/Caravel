# A script to automatically fetch, bundle, process and combine mangadex links into a collection of epub files

Features to add from simplest to final details:

- DONE use KCC from python on an image folder to make an epub with appropriate parameters
- ~~convert bulk cbz to image folders in correct order~~ No longer needed
- DONE using bulk ~~cbz~~ images directly from mangadex, push metadata appropriately for author, series, chapter, and volume.
- DONE automatically fetch  raw images from mangadex from a series name~~, link, or mangadex id~~
- Integrate calibre to add to digital library (Partially integrated)
- Add support for other sites, or piggy back on another download system
- Add support to use anilist or mal IDs to fetch manga

Nice steps, but not necessary:

- Add gui
- web add-on?
- how to go through kobosync?
- Reverse kobosync to use anilist api to update reading progress?
- see if there's a way to request mangas from the tablet

## Scope

- fetch manga from mangadex
DONE - convert to epub
- push to calibre
Additional but not necessary:
- fetch manga from other sites
- a gui or web interface
- syncing to tablet
- syncing reading progress to anilist
