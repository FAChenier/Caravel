# This script consolidates KCC tasks for converting comic files to an EPUB files

import os

def img_dir_to_epub(series_path: str, volume_id: int, verbose = True, delete = True, tablet_profile = "KoL") -> dict:
    """Executes a KCC (Kindle Comic Converter) command to convert a folder of images to an EPUB file.

    Note that a folder cannot contain illegal characters. This function assumes that the folder has a clean name. ie, for "Blame! Vol. 1", the folder name should be "Blame Vol. 1"
    This also implies that the folders are already created. This function WILL NOT create any folder.
    The function follows the structure that mangadex_retriever.py creates. See that script for more details.
    This function will execute a KCC CLI command. See https://github.com/ciromattia/kcc/releases/tag/v5.6.2, get "kcc-c2e_5.6.2.exe", rename to "kcc-c2e.exe", add to PATH.

    The working directory structure should be as follows:
    workdir
    > /book_series_1
    > /book_series_2 (ie, "Blame")
        > /book_series_2_volume (ie, "0001", representing volume 1)
        > /book_series_2_title (ie, "0002")
            > /book_series_2_title_chapter_1 (ie, "1", depending on naming scheme of the source)
            > /book_series_2_title_chapter_2 (ie, "1.5", example of an unusual naming scheme, Windows keeps it in the right order)
                > /book_series_2_title_chapter_2_page_1 (ie, "00001.png")
                > /book_series_2_title_chapter_2_page_2 (ie, "00002.png")
                > ...

    Where the main arguments to this function are:
    - The path to BOOK SERIES, not workdir! (ie: .../workdir/book_series_2)
    - The volume ID of the colume INSIDE the series folder that we want to convert (ie: 2 = third ordered folder inside .../workdir/book_series_2)

    Args:
        series_path (str): Directory (using \\ in path) in which volume folders are located.
        volume_id (int): ID of the volume to convert from an ordered list inside the series folder. mangadex_retriever.py creates them in order, ie: "0001", "0002", "0003", etc. "stranded" may also exist
        delete (bool, optional): Whether to delete the original folder after conversion. Defaults to True.
        verbose (bool, optional): Whether to print messages to the console. Defaults to True.
        tablet_profile (str, optional): Profile to use for the conversion. Defaults to "KoL" (Kobo Libra 2 or H20). See VALID_TABLET_PROFILES for a list.
    Returns:
        dict: Dictionary containing the following keys: "success" (bool), "full_path" (str), "error" (str).

    Where "success" is True if the conversion was successful, and "full_path" is the full path to the converted file (which will be a .EPUB). Will be path to folder that failed if "success" is False.
    "error" will be a string containing the error message if "success" is False, or a string with assumptions for any invalid inputs even if "success" is True.

    List of errors:
    - SERIES_FOLDER_DOES_NOT_EXIST: The series folder does not exist inside the filesystem
    - VOLUME_ID_NOT_INTEGER: The volume ID is not an integer. Only sent if it couldn't be converted to an integer
    - VOLUME_ID_OUT_OF_LOW_BOUNDS: The volume ID is less than 0. Not making assumptions so this will abort
    - VOLUME_ID_OUT_OF_HIGH_BOUNDS: The volume ID is greater than the number of volumes in the series folder. Not making assumptions so this will abort
    - DELETE_NOT_BOOLEAN: The "delete" parameter is not a boolean. Defaulting to False for safety
    - TABLET_PROFILE_NOT_STRING: The "tablet_profile" parameter is not a string. Defaulting to empty string, but may result in undesired output, so it also disables "delete"
    - TABLET_PROFILE_NOT_VALID: The "tablet_profile" parameter is not a valid profile. See VALID_TABLET_PROFILES for a list. Also disables "delete", see above
    - VOLUME_IS_ALREADY_AN_EPUB: The volume folder is not a valid volume folder, but an EPUB with the same name exists. This is likely a bug in the script, please report it
    - VOLUME_FOLDER_DOES_NOT_EXIST: The volume folder does not exist inside the filesystem
    - VOLUME_FOLDER_IS_EMPTY: The volume folder is empty. Either a bad input or mangadex_retriever.py aborted and this still passed. Not making assumptions so this will abort
    - KCC_STEP_FAILED: The KCC command failed to execute or the file failed to rename. This is a big step where many things can go wrong, hopefully this never happens
    - CATASTROPHIC_ERROR: A catastrophic error occured in the script. See console for details. This is likely a bug in the script, please report it
    """

    final_error_msg = "" # This will be the final error message if some inputs are invalid or assumptions are made
    if not type(verbose) is bool:
        print("Error: " + str(verbose) + " is not a valid value for 'verbose', must be BOOLEAN. Defaulting to True")
        verbose = True

    try:
        # Start by validating input and exiting or asking for new inputs if they are invalid:
        if not os.path.isdir(series_path):
            # Make sure the series folder exists
            print("Error: " + series_path + " is not a valid directory, series folder does not exist") if verbose else None
            return {
                "success": False,
                "full_path": '"' + series_path + '" does not exist',
                "error": "SERIES_FOLDER_DOES_NOT_EXIST"
                }

        if not type(volume_id) is int:
            # Make sure the volume is a number
            try:
                volume_id = int(volume_id) # If this works, keep going. volume_id likely entered as float or string
            except:
                print("Error: " + str(volume_id) + " is not a valid volume ID, must be INTEGER") if verbose else None
                return {
                    "success": False,
                    "full_path": series_path,
                    "error": "VOLUME_ID_NOT_INTEGER"
                    }

        if volume_id < 0:
            # Make sure the volume is a positive number, ids are 0-indexed
            print("Error: " + volume_id + " is not a valid volume ID, must be POSITIVE") if verbose else None
            return {
                "success": False,
                "full_path": series_path,
                "error": "VOLUME_ID_OUT_OF_LOW_BOUNDS"
                }

        if volume_id >= len(os.listdir(series_path)):
            # Make sure the volume is not out of bounds
            print("Error: " + volume_id + " is not a valid volume, must be less than " + str(len(os.listdir(series_path))) + " (Entered is out of bounds)") if verbose else None
            return {
                "success": False,
                "full_path": series_path,
                "error": "VOLUME_ID_OUT_OF_HIGH_BOUNDS"
                }

        # Check other parameters too, like tablet_profile, delete, etc. if needed. Create a final error message for assumptions made with invalid inputs
        if not type(delete) is bool:
            # Make sure "delete" is a boolean
            print("Error: " + str(delete) + " is not a valid value for 'delete', must be BOOLEAN. Defaulting to False") if verbose else None
            final_error_msg += "DELETE_NOT_BOOLEAN, "
            delete = False

        if not type(tablet_profile) is str:
            # Make sure "tablet_profile" is a string
            print("Error: " + str(tablet_profile) + " is not a valid value for 'tablet_profile', must be STRING. Defaulting to empty string") if verbose else None
            final_error_msg += "TABLET_PROFILE_NOT_STRING, "
            tablet_profile = ""
            delete = False # If the profile is invalid, we don't want to delete the original folder in case the output is not what we want
        else:
            # Tablet was specified but check if it's valid:
            VALID_TABLET_PROFILES = ["K1", "K2", "K34", "K578", "KDX", "KPW", "KPW5", "KV", "KO", "K11", "KS", "KoMT", "KoG", "KoGHD", "KoA", "KoAHD", "KoAH2O", "KoAO", "KoN", "KoC", "KoL", "KoF", "KoS", "KoE"]
            if not tablet_profile in VALID_TABLET_PROFILES:
                print("Error: " + str(tablet_profile) + " is not a valid value for 'tablet_profile'. Defaulting to empty string") if verbose else None
                final_error_msg += "TABLET_PROFILE_NOT_VALID, "
                tablet_profile = ""
                delete = False # If the profile is invalid, we don't want to delete the original folder in case the output is not what we want


        # If we didn't exit, the inputs SHOULD be valid. We haven't tried checking if the directories exist yet though
        # First, get the variants we need to work with paths:
        book_title = os.path.basename(series_path) + " - Vol. " + str(volume_id+1) # This will exclude illegal characters, but they are allowed in the metadata later
        volume_text = os.listdir(series_path)[volume_id] # listdir is 0-indexed, should be converted before passing this if needed. We do this because "1" may not be the first volume
        inside_workdir = os.path.join(series_path, volume_text)

        if not os.path.isdir(inside_workdir):
            # Make sure the volume folder exists
            # It might have failed previously, so check if there's an EPUB and report it if so:
            if os.path.isfile(os.path.join(series_path, book_title + '.epub')):
                print("Error: " + inside_workdir + " is not a valid volume directory, volume folder does not exist. An EPUB with the same name exists, aborting.") if verbose else None
                return {
                    "success": False,
                    "full_path": os.path.join(series_path, book_title + '.epub'),
                    "error": "VOLUME_IS_ALREADY_AN_EPUB"
                    }
            else:
                print("Error: " + inside_workdir + " is not a valid volume directory, volume folder does not exist") if verbose else None
                return {
                    "success": False,
                    "full_path": series_path,
                    "error": "VOLUME_FOLDER_DOES_NOT_EXIST"
                    }

        if len(os.listdir(inside_workdir)) == 0:
            # Check if the folder is empty
            print("Error: " + inside_workdir + " is empty, is this the right folder?") if verbose else None
            return {
                "success": False,
                "full_path": series_path,
                "error": "VOLUME_FOLDER_IS_EMPTY"
                }

        # By now, we should be pretty sure that we have all that we need. We can start the conversion process.
        # Prepare the KCC CLI command and include all related specified parameters:
        kcc_command = 'kcc-c2e --manga-style' + (' --profile "' + tablet_profile + '"' if tablet_profile != "" else "") + ' --upscale --stretch --mozjpeg --title "' + book_title + '" --format EPUB --hq' + (' --delete "' + inside_workdir +'"' if delete else ' "' + inside_workdir +'"')
        # Interesting parameters for later:
        # --batchsplit 2: consider every subdir as a volume. This might be good to process the entire workdir at once
        # --output OUTPUT: output to OUTPUT instead of the current directory (?)
        try:
            os.system(kcc_command)
            # Profile makes it into a .kepub.epub, change it back:
            os.rename(os.path.join(series_path, volume_text + '.kepub.epub'), os.path.join(series_path, volume_text + '.epub'))
            # At this point, we have a simple epub containing all book content and correctly formated, profivided the images and chapters were in a clean order
            print('Converted folders to epub') if verbose else None
            final_error_msg = final_error_msg[:-2] # Remove the last ", " from the final error message
            return {
                "success": True,
                "full_path": os.path.join(series_path, book_title + '.epub'),
                "error": final_error_msg
                }
        except Exception as e:
            print('Failed passing kcc command or renaming the file, aborting.\nFILES MAY HAVE BEEN DELETED, CORRUPTED, OR CREATED.\nSee below for details:') if verbose else None
            print('Error: ' + str(e)) # This will always print because it is helpful in debugging. May be changed later
            return {
                "success": False,
                "full_path": series_path,
                "error": "KCC_STEP_FAILED"
                }

    except Exception as e:
        print('Catasrophic error in "kcc_conversion.py", aborting. See below for details:') if verbose else None
        print('Error message up to failure:\n' + final_error_msg) # This will always print because it is helpful in debugging. May be changed later
        print("Error: " + str(e)) # This will always print because it is helpful in debugging. May be changed later
        return {
            "success": False,
            "full_path": "",
            "error": "CATASTROPHIC_ERROR"
            }