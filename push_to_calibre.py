# Send book to Calibre

import os
from settings import use_calibre, calibre_path

def push_to_calibre(epub_path: str, author: list, series: str, volume: float, title: str, cover_path: str) -> dict:
    """Aggregate all required data to push a book to Calibre alongside relevant metadata
    FIXME CALIBRE MUST BE CLOSED FOR THIS TO WORK

    Args:
        epub_path (str): Location of the epub file to push using "\\" as a separator
        author (list): Author list of the book, each other is a string in a list
        series (str): Name of the book series if it has one
        volume (float): Volume number (as a float) in the series if it has one
        title (str): Real title of the book
        cover_path (str): Path to an image file of the book's cover, using "\\" as a separator
    Returns:
        dict: Dictionary containing the data: {"success": bool, "book id": int, "error": str}
    Where "success" is a boolean indicating whether the operation was successful, (TODO) "book id" is the id of the book in Calibre's database, and "error" is a string containing the error message if the operation failed
    """
    error_message = ''

    # First, go over author list and format a string out of it if it's not empty:

    if use_calibre != False:
        if len(author) > 0:
            try:
                author = ' & '.join(author)
            except:
                author = ''
                error_message += 'AUTHOR_LIST_ERROR, '
                print('Author is list parameter failing, ignoring')
        else:
            author = ''
            error_message += 'AUTHOR_EMPTY, '
            print('Author list is empty, ignoring')

        # Check if series is a string:
        if type(series) != str:
            series = ''
            error_message += 'SERIES_NOT_STRING, '
            print('Series is not a string, ignoring')

        # Repeat for title:
        if type(title) != str:
            title = ''
            error_message += 'TITLE_NOT_STRING, '
            print('Title is not a string, ignoring')

        # Then, check if the series has a volume number and format it accordingly:
        if volume != '':
            try:
                volume = float(volume)
            except:
                volume = ''
                error_message += 'VOLUME_NOT_FLOAT, '
                print('Volume "' + str(volume) + '" is not a float, ignoring')

        # Now check if epub and cover paths are correctly formatted and exist:
        if type(epub_path) != str:
            print('EPUB path "' + str(epub_path) + '" is not a string')
            return {"success": False, "book id": None, "error": error_message + ', EPUB_NOT_STRING'}
        if type(cover_path) != str:
            print('Cover path "' + str(cover_path) + '" is not a string')
            return {"success": False, "book id": None, "error": error_message + ', COVER_NOT_STRING'}

        if not os.path.exists(epub_path):
            print('EPUB path "' + str(epub_path) + '" does not exist')
            return {"success": False, "book id": None, "error": error_message + ', EPUB_NOT_EXIST'}
        if not os.path.exists(cover_path):
            print('Cover path "' + str(cover_path) + '" does not exist, ignoring')
            cover_path = ''
            error_message += 'COVER_NOT_EXIST, '


        # If we get to here, we can be pretty sure everything is valid. Build the command based on the parameters:
        calibre_push = 'calibredb add ' + ('--authors "' + author + '" ' if author != '' else '') + ('--series "' + series + '" ' if series != '' else '') + ('--series-index ' + str(volume) + ' ' if volume != '' else '') + ('--title "' + title + '" ' if title != '' else '') + ('--cover "' + cover_path + '" ' if cover_path != '' else '') + '"' + epub_path + '"'

        try:
            # TODO: Remove library path hardcoding
            # TODO: Make this wokr with Calibre open
            calibre_push = 'calibredb add ' + ('--authors "' + author + '" ' if author != '' else '') + ('--series "' + series + '" ' if series != '' else '') + ('--series-index ' + str(volume) + ' ' if volume != '' else '') + ('--title "' + title + '" ' if title != '' else '') + ('--cover "' + cover_path + '" ' if cover_path != '' else '') + '"' + epub_path + '"'
            os.system(calibre_push)
            print('Calibre push successful')
            return {"success": True, "book id": None, "error": error_message[:-2]}
        except:
            print('Calibre push failed')
            return {"success": False, "book id": None, "error": error_message + ', CALIBRE_PUSH_FAILED'}
    else:
        print('Calibre push disabled, skipping...')
        return {"success": True, "book id": None, "error": "CALIBRE_DISABLED"+error_message[:-2]}
