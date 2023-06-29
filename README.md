# Caravel

Caravel is a python script/program that allows you to download a series of manga volumes through the Mangadex API.

## Usage

Requires Python 3.10. Lower versions have not been tested but could work. In case you don't know, install Python through the Microsoft Store on Windows. Untested on any other platforms.

1. Put all the files in this repo inside a folder
2. Ensure that `kcc_c2e.exe` is in PATH. See `kcc_conversion.py` for information on how to set that up.
3. Review `settings.py` and change as needed. Note that not all settings are implemented.
4. Run `mangadex_retriever.py` and follow the CLI instructions.

The script will attempt to push to an ebook management software called Calibre. The script also defaults to converting for a Kobo Libra 2. As of now, these things can't be changed but with enough knowdlegde you should be able to find the lines you need to change to adapt this script for your needs.

> Important:
> Calibre MUST BE CLOSED and all content servers MUST BE SHUT DOWN for the `calibredb add` command to pass, else it will complain. Not a big issue for me right now so there are no fixes planned.

## Currently Working

- Search Mangadex.org for a manga using a title search
- Select one of the results in the manga search
- Select which volumes of the series to download
- Automatically fetch most prominent metadata and cover
- Push to Calibre

## NOT Currently Working

- Handling manga that don't use volumes
- Reporting back to Mangadex if the content server is unhealthy (images are corrupted)
- VERY LIMITED TESTING
- MINIMAL ERROR HANDLING

If you get any problems, create an issue or just try to fix it and let me know how it goes. Thanks!

## Notes

This is a small project and I am not a programmer, I'm doing this for fun but if you have any feedback or suggestions I'd be more than happy to learn and apply them. Thanks!
