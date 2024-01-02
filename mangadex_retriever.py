# We want to stop relying on external services to download. Call Mangadex directly
# https://api.mangadex.org/docs/retrieving-chapter/
# https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-tag

# Page above will explain in stunning detail how to do it. Just load it and store the images. Do what they ask for and so on.
# Might also be able to pull some metadata.

# This should be done before other metadata mapping so that we have a solid basis that wont change further.

# Requirements:
# - Mangadex just wants to know the "chapter ID". This is the ID of the chapter in the chapter list.
# That's it

# A chapter is a unique bundle of images. A volume may be associated to it. There are also multiple languages. We want to only request english, and avoid duplicate chapters.
# So we also need to:
# - Identify the manga on mangadex
# - Determine if it is available in english
# - Determine which scanlation group to use if more than one (use the one with the most chapters in the entire series, or only one available)

# We would also like to separate the chapters into volumes. Research the API further to see if this is doable. It will depend on proper formating from scanlaters, but usually they are good about it.

# Since we want to use anilist for metadata, being able to crossmatch Anilist and Mangadex entries would be nice. See their respective API...
# See https://api.mangadex.org/docs/static-data/ in section 'Manga links data', Mangadex may declare where the manga is in Anilist, can we reverse it?
# Answer: No, but we can use it to confirm. Using Anilist titles in a search seems ok
# Basically: Anilist -> Title search in Mangadex -> Confirm correct manga by going back to anilist

# For now, only search unsing inputted title

# Some of this code is using https://api.mangadex.org/docs/guide/find-manga/ as a reference

import concurrent.futures
import os
import time
from pprint import pprint

import requests

from func import *
from kcc_conversion import img_dir_to_epub as kcc_convert
from misc_utils import download_chapter_image, link, printProgressBar
from nav import *
from push_to_calibre import push_to_calibre as calibre_push
import time

# ====================================================================================================
# ? Start by getting the title to lookup
title_lookup = title_search_nav() # ! This function does an API request!

# ====================================================================================================
# ? Now do the search and show the results, then ask the user which to use
user_select = series_select_nav(title_lookup) # ! This function MAY make an API request!

# ====================================================================================================
# * All of these below are for compatibility, they should be replaced later on
us = user_select # Shortcut for later
id_select = int(us['response']) - 1

title_list = title_lookup["titles_results"][id_select]
id_list = title_lookup["ids_results"][id_select]
md_link_list = title_lookup["mangadex_links"][id_select]
al_link_list = title_lookup["anilist_links"][id_select]
authors_list = us["contributors"]["names"]

# ====================================================================================================
# We now have a title to work with. We need to get the ID of the manga on Mangadex to continue
print('\n\n\n')
# TODO make this its own navigation function that supports going back and exiting
chapter_request = chapter_request_and_files(us['mdid'], us['clean_title']) # ! This function does an API request!
cr = chapter_request # Shortcut for later
# TODO: An alternative to above is to allow the user to select which scanlator to use if a choice is available.
# TODO: Cache requests if they have been made within the last 10 minutes or so. This will reduce load on Mangadex and speed up the process

chapter_id_list = cr['chapter_id_list']

build_folders(cr["pseudo_file_structure"])

volume_selection = select_volumes_to_download(cr['pseudo_file_structure'])
vs = volume_selection # Shortcut for later
volume_list = vs['volumes_to_download']

cover_request_and_download(us['mdid'], cr['pseudo_file_structure'], vs['volumes_to_download'])

# ====================================================================================================

# Now we have a list of volumes to download, we can go through the pseudo_file_structure and download the chapters based on Mangadex IDs
vols = 0
for volume in volume_list:
    vols += 1
    print(
        '\n\n========================================',
        'Downloading Volume ' + str(vols) + " of " + str(len(volume_list)),
        '========================================', sep='\n'
        )

    # First, check if the chapter already exists. If so, skip creating it
    volume = str(volume) # * compatibility during the upgrade to functions
    workdir = os.path.join(os.getcwd(), "books", us['clean_title']) # * compatibility during the upgrade to functions

    volume = volume.zfill(4)
    vol_path = os.path.join(workdir, volume)
    if not os.path.exists(vol_path):
        os.mkdir(vol_path)

    # Create each chapters inside the volume folder. A chapter is a folder in which we'll put the images. Name it the same is pseudo_file_structure
    chaps = 0
    for chapter in cr['pseudo_file_structure'][us['clean_title']][volume]:
        chaps += 1
        print('Starting Chapter ' + str(chaps) + " of " + str(len(cr['pseudo_file_structure'][us['clean_title']][volume])))
        ch_path = os.path.join(workdir, volume, chapter)
        if not os.path.exists(os.path.join(workdir, volume, chapter)):
            os.mkdir(os.path.join(workdir, volume, chapter))
        # Now we have a chapter folde, we need to get the chapter ID from pseudo_file_structure
        chapter_id = cr['pseudo_file_structure'][us['clean_title']][volume][chapter]

        retry_count = 0
        while retry_count < 3:
            chapter_request = requests.get(f"{baseUrl}/at-home/server/{chapter_id}")
            response = chapter_request.json()

            if 'errors' in response and response['result'] == 'error' and response['errors'][0]['detail'] == 'Rate Limit Exceeded':
                retry_count += 1
                print('Rate limit exceeded, retrying in 100ms')
                time.sleep(0.1)  # Retry after 100ms
            else:
                break

        # Now we have the image data, we can get the images
        im = 0
        # pprint(chapter_request.json())
        total_images = len(chapter_request.json()['chapter']['data'])
        chapter_baseUrl = chapter_request.json()['baseUrl']
        chapter_hash = chapter_request.json()['chapter']['hash']

        print(
            '========================================',
            'Downloading ' + str(total_images) + ' Images', sep='\n'
            )
        time_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for image in chapter_request.json()['chapter']['data']:
                # Check if the image already exists. If so, skip it. If first image, ask if we should overwrite (TODO)
                if os.path.exists(os.path.join(workdir, volume, chapter, str(im).zfill(5))+".png") or os.path.exists(os.path.join(workdir, volume, chapter, str(im).zfill(5))+".jpg"):
                    # Image already exists, skip it
                    continue
                else:
                    image_path = os.path.join(workdir, volume, chapter, str(im).zfill(5))
                    # Build the URL to the image, download it, then save it.
                    # im_url = chapter_baseUrl + '/data/' + chapter_hash + '/' + image                        # Build the URL to the image
                    # image_request = requests.get(im_url)                                       # Get the downloaded image extension
                    # with open(os.path.join(workdir, volume, chapter, str(im).zfill(5))+'.png', 'wb') as f: # Save the image
                    #     f.write(image_request.content)
                    executor.submit(download_chapter_image, chapter_baseUrl, chapter_hash, image, image_path)
                    time.sleep(0.2) # Sleep for 0.1 seconds to avoid getting rate limited
                    #download_chapter_image(chapter_baseUrl, chapter_hash, image, image_path)
                printProgressBar(im, total_images, prefix = 'Progress:', suffix = 'Complete', length = 50)
                im+=1

                # TODO: Mangadex expects a PUSH to report if the provided link was good or not. Do when possible

                # Last, rename the image to something simple to avoid breaking the filesystem, use 00001, 00002, etc should be enough
                #os.rename(os.path.join(workdir, volume, chapter, image), os.path.join(workdir, volume, chapter, str(im).zfill(5) + '.' + image_extension))


        # All images downloaded, go to next chapter
        printProgressBar(total_images, total_images, prefix = 'Progress:', suffix = 'Complete', length = 50) # Ducktape fix to make sure the progress bar is full lol
        time_end = time.perf_counter()
        print('Time to download: ' + str(round(time_end - time_start, 2)) + ' seconds')
        print(
            'Finished downloading Chapter ' + str(chaps),
            '========================================', sep='\n'
            )

    # All Chapters finished, convert it to epub before moving on to next volume
    print(
        'Finished downloading Volume ' + str(vols) + " of " + str(len(volume_list)),
        '========================================', sep='\n'
        )
    # Start converting using kcc_conversion.py
    # Need to convert volume's name to volume's ID as it appears at this moment inside the series folder:
    volumes_in_dir = os.listdir(workdir)
    # Find the list ID of volume we just downloaded:
    vol_id = volumes_in_dir.index(volume)

    print(
        'Starting conversion...',
        '========================================', sep='\n'
        )

    #First, check if the volume is already converted. If so, skip it:
    if os.path.exists(os.path.join(workdir, volume.zfill(4)+'.epub')):
        print('Volume already converted, skipping')
        kcc_results = {"success": True, "full_path": os.path.join(workdir, volume.zfill(4)+'.epub'), "error": ''}
    else:
        # Convert it
        kcc_results = kcc_convert(workdir, vol_id, True, False) # This should now be chill even if we delete folders as we update the vol_id each time

    print(
        '========================================\n',
        'Conversion was ' + 'successful!\n' if kcc_results["success"] else 'unsuccessful...\n',
        'Error message: ' + kcc_results["error"] + '\n' if kcc_results["error"] != '' else '',
        '========================================', sep=''
        )

    if kcc_results['success']:
        # Push it to Calibre if conversion was successful
        try:
            volume = int(volume)
        except:
            volume = 'Extra'

        try:
            # Get the cover path
            cover_path = os.path.join(workdir, str(volume).zfill(4)+'.jpg')
        except:
            # No cover found, use default
            cover_path = ''

        # Calibre must be closed for this to work
        push_results = calibre_push(
            os.path.join(workdir, str(volume).zfill(4) + '.epub'),
            authors_list,
            us['series_title'],
            volume,
            'Vol. '+ str(volume) + ' - ' + us['series_title'],
            cover_path
        )
        # Can't clean up folder as Calibre could fail but report success. If we don't delete anything, we'll get to a point where all steps get skipped anyway

# Finished the job
print(
    'Finished downloading all volumes',
    '========================================\n\n', sep='\n'
    )

# At this point, running this script, we went from entering a title search to having ebooks of requested volumes.
# TODO: Adapt for manga that don't use volumes. Maybe use chapter ranges? ie "Series Title - Ch.20-30.epub"
# TODO: Make this a function that is called rather than the script to run
# TODO: Include exception handling, error reporting, and attempts for data correction
# TODO: Report back to Mangadex for image download success or failure
# TODO: Allow disabling verbose CLI output
# TODO: More general, but allow the user to navigate the steps instead of locking them in a workflow and having to Ctrl+C out of it if they make a mistake
