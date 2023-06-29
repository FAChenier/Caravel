# A script to automatically fetch, bundle, process and combine mangadex links into a collection of epub files

# features to add from simplest to final details:
# - use KCC from python on an image folder to make an epub with appropriate parameters
# - convert bulk cbz to image folders in correct order
# - using bulk cbz directly from mangadex, rename appropriately for author, series, chapter, and volume before converting to image folders. Then, order then into folders by volume before converting to epubs
# At this point, we can dump bulk downloads into a folder and have it automatically convert to epubs
# - automatically fetch cbz (or raw images?) from mangadex from a series name, link, or mangadex id
# Should step above be through the api or some other project?
# - automatically fetch cbz (or raw images?) from mangadex from a list of series names, links, or mangadex ids
# - integrate calibre to add to digital library
# Should research calibre tools, like adding metadata or cover
# - integrate calibre to add to digital library with metadata and cover
# - add support for other sites, like mangasee, mangakakalot, etc
# Maybe use tachiyomi sources for this?
# - add support to use anilist or mal IDs to fetch manga
# Nice steps, but not necessary:
# - add gui or web interface?
# - web add-on?
# - how to go through kobosync?
# - Reverse kobosync to use anilist api to update reading progress?
# - see if there's a way to request mangas from the tablet

# Scope:
# - fetch manga from mangadex
# DONE - convert to epub
# - push to calibre
# Additional but not necessary:
# - fetch manga from other sites
# - a gui or web interface
# - syncing to tablet
# - syncing reading progress to anilist


# ================================================================================================================================
# ================================================================================================================================
# OLD CODE, IGNORE THIS. For reference only
# ================================================================================================================================
# ================================================================================================================================

# import os
# from kcc_conversion import img_dir_to_epub as kcc_convert
# from tkinter import filedialog
# from push_to_calibre import push_to_calibre as calibre_push

# #workdir = input("Enter the directory to work in: ")
# #workdir = workdir.replace("\\", "/")
# # Now we have a directory to work in, we should place the "volume" folders in here until they are converted to epubs and subsequently deleted


# if __name__ == "__main__":

# # ================================================================================================================================
# # This section is to find the location of what we want to convert. This could be its own function or a GUI or something like that.
# # ================================================================================================================================
#     workdir = "C:\\Users\\capit\\OneDrive\\Documents\\GitHub Projects\\Caravel\\books" # TODO: Make this an input
#     # List the book series so that we can go down to the volume list:
#     # item_list = os.listdir(workdir)
#     # Ask user which book to series to access:
#     # print('Selected directory: ')
#     # i = 0
#     # for item in item_list:
#     #     i += 1
#     #     # List how many volumes in each item:
#     #     try:
#     #         vols = len(os.listdir(os.path.join(workdir, item)))
#     #     except:
#     #         vols = 0
#     #     print(str(i) + ": " + item + " (" + str(vols) + " items)")
#     # # Select the folder to enter:
#     # to_convert = int(input('ID of folder to enter: ')) - 1
#     # TODO Make this exclude non-folders. Careful though, kcc_conversion.py uses the ID based on the position, so change it there too
#     book_dir = ''
#     while book_dir == '':
#         book_dir = filedialog.askdirectory(initialdir=workdir, title="Select a Series Folder")
#     # .askdirectory(initialdir=workdir, title="Select a folder")
#     # Instead of using a CLI menu, use a dialog box to select the a folder item inside workdir:


#     # workdir = os.path.join(workdir, item_list[to_convert])

#     # First, identify the blame_vol9 folder inside workdir:
#     # TODO: Convert to filedialog too, but be careful with how kcc_conversion.py uses the ID based on the position, so change it there too
#     item_list = os.listdir(workdir)
#     print('\n\nSelected Volume to Convert: ')
#     i = 0
#     for item in item_list:
#         i += 1
#         # List how many chapters in each item:
#         try:
#             chaps = len(os.listdir(os.path.join(workdir, item)))
#         except:
#             chaps = 0
#         print(str(i) + ": " + item + " (" + str(chaps) + " items)")
#     # Select the folder to convert:
#     to_convert = input('ID of folder to convert, separated by commas: ')
#     # TODO Make this exclude non-folders. Careful though, kcc_conversion.py uses the ID based on the position, so change it there too (same as above)
#     # TODO: Make it so that it can be a folder or a cbz file

# # =========================================================================================================================================
# # This section messes with filenames and decompresses folders. This is not needed anymore since we use mangadex_reader.py to get raw images
# # =========================================================================================================================================

#     # Now we have the folders to convert, we can change the working directory to it every time:
#     for to_convert in to_convert.split(','):
#         to_convert = int(to_convert) - 1
#         inside_workdir = os.path.join(workdir, item_list[to_convert])

#         # Loop through each file and replace the .cbz extension with .zip:
#         # for file in os.listdir(inside_workdir):
#         #     if file.endswith(".cbz"):
#         #         os.rename(os.path.join(inside_workdir, file), os.path.join(inside_workdir, file.replace(".cbz", ".zip")))
#         # print('Converted cbz to zip')

#         # Now we have a folder with zip files, we can convert them to folders:
#         # for file in os.listdir(inside_workdir):
#         #     if file.endswith(".zip"):
#         #         os.system('7z x "' + os.path.join(inside_workdir, file) + '" -o"' + os.path.join(inside_workdir, file.replace('.zip', '')) + '" -bso0 -bsp0 -bse0')

#                 # Check if the zip was successfully extracted and delete the original if so:
#                 # TODO: Move to an archive folder instead, and revert if there's an error later on
#                 # if os.path.isdir(os.path.join(inside_workdir, file.replace('.zip', ''))):
#                 #     os.remove(os.path.join(inside_workdir, file)) # danger
#         # print('Converted zip to folders')

#         # Folders often have attrociously long names:
#         # name_reducer(inside_workdir)
#         # ^ Not needed since mangadex_reader.py isn't moronic

# # ===============================================================================
# # This section converts the folders to epubs using calibre and kcc_conversion.py
# # Note that it's still inside the for-loop from the previous section!
# # ===============================================================================

#         # Now we have a folder with folders, we can convert them to epubs:
#         kcc_success = False
#         while not kcc_success:
#             results = kcc_convert(workdir, to_convert, False)
#             if not results["success"]:
#                 print("Error converting to epub:\n"+results["error"])
#                 if input('Do you want to try again? (y/n): ') == 'y':
#                     continue
#                 else:
#                     print("Aborting...")
#                     # Later on, we can try to fix the error and try again. For now, abort
#                     pass # Skip to the next volume. TODO: At the end, return the outcome of the script and any errors like this.
#                 # Also make it clean up its mess if we can confirm nothing was deleted
#             else:
#                 kcc_success = True
#                 print(results["full_path"])
#                 if results["error"] != "":
#                     print("Warning(s) during conversion:\n"+results["error"])


#         # NOTE: Should split this script into functions and call them from a main function

# # ====================================================================================================
# # This section finishes up with a few annoying manual inputs. Still inside the for-loop from earlier.
# # This is to prepare the information and metadata to push to calibre
# # ====================================================================================================

#         # Try pushing to calibre:
#         # calibredb add --authors AUTHORS --cover PATH_TO_COVER --series SERIES --series-index VOLUME_NUMBER --title TITLE PATH_TO_EPUB
#         # calibredb add --authors "Tsutomu Nihei" --cover "C:\Users\capit\OneDrive\Documents\GitHub Projects\Caravel\books\BLAME!\[SAME NAME].jpg" --series "BLAME!" --series-index 9 --title "BLAME! Vol. 9" "C:\Users\capit\OneDrive\Documents\GitHub Projects\Caravel\books\BLAME!\blame_vol9.epub"
#         # A lot of this will depend on the naming format of the files.
#         # If I download from TachiJ2K, it will have the name of the series as the main folder and every chapter below that with name as "scanlator_Vol.n Ch.n - title"
#         # If I download from https://manga.danbulant.eu/, it depends on the options and will be anmed by the series name and contain the chapter names.

#         # For now, using the optimal format provided by TachiJ2K to extract metadata to push to calibre:
#         # example epub filename to import: BLAME!_Vol.10.epub
#         epub_path = results["full_path"] # name hasn't changed
#         # Use workdir as series name and image folder name as volume number
#         series = os.path.basename(workdir)
#         volume = os.path.basename(inside_workdir)
#         title = "Vol. " + str(int(volume)) + " - " + series
#         # Now we would be missing the author and cover, which we need to get from the internet
#         # To do this, we use the anilist API (author and cover)
#         # Get cover: Media.coverImage {large}
#         # Get author: Media.staff {nodes {name {full}}}
#         # For now though, enter manually:
#         author = input('Enter author: ')
#         # Cover, just use any png EITHER jpg file with the same name as the epub in the same folder:
#         ty = input('Ensure the cover has the same name as the file and is in the same folder.\nWhat is the extension of the cover? (j:jpg or p:png): ')
#         ty = "jpg" if ty == "j" else "png"
#         cover = os.path.join(workdir, item_list[to_convert] + '.'+ ty)

# # ====================================================================================================
# # Push to calibre. This is also inside the for-loop from earlier. Should be done for cleanly than
# # through an os.system(). Can be done programatically I think, but not researched yet.
# # ====================================================================================================

#         push_result = calibre_push(author, series, volume, title, cover, epub_path)
#         if push_result["success"]:
#             print("Successfully pushed to calibre. Cleaning up...")
#             # Clean up and delete the cover and epud:
#             os.remove(os.path.join(workdir, item_list[to_convert] + '.'+ ty))
#             os.remove(epub_path)
#         else:
#             print("Error pushing to calibre:\n"+push_result["error"])
#             print('Did not clean up. Please check the error and try again. Continuing to next volume...')
