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

from func import *
from nav import *
import requests
from pprint import pprint
import os
import time
import concurrent.futures
from misc_utils import printProgressBar, download_chapter_image, link
from kcc_conversion import img_dir_to_epub as kcc_convert
from push_to_calibre import push_to_calibre as calibre_push

user_search = title_search()
title_lookup = mangadex_titles_request(user_search['lookup'])

# ====================================================================================================

title_list = title_lookup["titles_results"]
id_list = title_lookup["ids_results"]
md_link_list = title_lookup["mangadex_links"]
al_link_list = title_lookup["anilist_links"]
authors_list = title_lookup["contributors"]

# TODO: Make this a loop so that it keeps asking until it has a valid result to use or user exits
user_select = display_results(title_lookup)
us = user_select # Shortcut for later

# ====================================================================================================
# We now have a title to work with. We need to get the ID of the manga on Mangadex to continue
chapter_request = chapter_request_and_files(us['mdid'], us['clean_title'])
cr = chapter_request # Shortcut for later
# FIXME Find a way to exclude official publishers from the list as we cant download from them, but often there is a scanlator version available
# TODO: An alternative to above is to allow the user to select which scanlator to use if a choice is available.
# TODO: Cache requests if they have been made within the last 10 minutes or so. This will reduce load on Mangadex and speed up the process
chapter_id_list = cr['chapter_id_list']

build_folders(cr["pseudo_file_structure"])

# To simplify the way we understand the file structure, we use a dictionary that represents it.
# When it's built, it will represent the potential file structure. We can then locate chapters without executing
# any additional requests to mangadex and hence reduce the load we are applying, even if marginal
# Note: "stranded" is a folder that will contain chapters that are not in a volume. FIXME if we find a manga that doesn't use volumes
# pseudo_file_structure = {us['clean_title']: {
#     'stranded': {},
# }}

# # Go through all chapter object and keep the ones we want. Build a file structure as we go
# for chapter in chapter_request.json()["data"]:
#     try:
#         work_chapter = chapter['attributes']['chapter']
#     except:
#         work_chapter = "No Chapter"

#     try:
#         work_volume = chapter['attributes']['volume']
#         text_volume = str(work_volume).zfill(4)
#     except:
#         work_volume = None
#         text_volume = 'Stranded'


#     # Check volume. If none, place in "stranded" folder. If volume, place in volume folder named simply "0001" where 1 is volume number. 10 is 0010 and so on
#     if work_volume == None:
#         # place in stranded folder, check if it already exists. If not, create it
#         stranded_path = os.path.join(workdir, 'stranded')
#         if not os.path.exists(stranded_path):
#             os.mkdir(stranded_path)
#         # Now we have a stranded folder, place the chapter in it
#         pseudo_file_structure[us['clean_title']]['stranded'][work_chapter] = chapter['id']
#         # This creates a pair inside the pseudo folder "stranded" such that: {chapter number: chapter ID} so we can easily find it later
#     else:
#         # Chapter has a volume, create a volume folder in workdir and pseudo_file_structure using volume number format above
#         volume_path = os.path.join(workdir, text_volume)
#         if not os.path.exists(volume_path):
#             os.mkdir(volume_path)
#         # Now we have a volume folder, place the chapter in it
#         # If volume not in the pseudo_file_structure, create it
#         if text_volume not in pseudo_file_structure[us['clean_title']]:
#             pseudo_file_structure[us['clean_title']][text_volume] = {}
#         pseudo_file_structure[us['clean_title']][text_volume][work_chapter] = chapter['id']
# # We should now have a map of where things belong

# # If everything ended up in stranded, that means the manga doesn't use volumes.
# # Instead of working with volumes, we will work with chapter ranges. For example, "Ch.20-30.epub" is a book containing chapters 20 to 30.
# # Check if everything is in stranded:
# if len(pseudo_file_structure[us['clean_title']]['stranded']) == len(chapter_id_list):
#     volume_list = []
#     # Everything is in stranded, we can work with chapter ranges:
#     print('Manga does not use volumes, using chapter ranges instead')
#     # Print a list of all chapters and ask user which ranges to download:
#     print('\nChapters found:')
#     x = 0
#     for chapter in pseudo_file_structure[us['clean_title']]['stranded']:
#         print(str(x) + ':\t' + chapter)
#         x += 1
#     # Now, ask user which ranges to download
#     ranges_to_download = input('Enter the ranges to download, separated by commas (ie: "11-20" or "11-20,21-30"): ')
#     if ranges_to_download == 'debug':
#         print('Entering Debug. Printing useful data...')
#         pprint(pseudo_file_structure)
#         print('Exiting Debug')
#         ranges_to_download = input('Enter the ranges to download, separated by commas (cannot enter DEBUG again): ')
#     range_list = ranges_to_download.replace(' ', '').split(',')
#     # Now we have ranges, we can build "volumes" in the pseudo_file_structure using the requested ranges. First range is a sort of volume 1, so inside folder "0001".
#     # Start by remaking pseudo_file_structure bu only for the requested chapters. All the others will be put in stranded again:
#     pseudo_file_structure = {us['clean_title']: {
#         'stranded': {},
#     }}
#     # Now we have a clean pseudo_file_structure, we can start building the ranges
#     x = 0
#     for chap_range in range_list:
#         x += 1
#         volume_list.append(str(x).zfill(4))
#         #meta_title = meta_title + ' - Ch.' + chap_range
#         meta_title = us["series_title"] + ' - Ch.' + chap_range
#         # Split the range into start and end
#         start = int(chap_range.split('-')[0])
#         end = int(chap_range.split('-')[1])
#         # Now we have a start and end, we can build the range
#         for chapter in chapter_request.json()["data"]:
#             try:
#                 work_chapter = chapter['attributes']['chapter']
#             except:
#                 work_chapter = -1

#             if work_chapter >= start and work_chapter <= end:
#                 # Chapter is in range, place it in the pseudo_file_structure
#                 pseudo_file_structure[us['clean_title']][x.zfill(4)][work_chapter] = chapter['id']
#             else:
#                 # Chapter is not in range, place it in stranded
#                 pseudo_file_structure[us['clean_title']]['stranded'][work_chapter] = chapter['id']
#         # Now we have a pseudo_file_structure that is built using chapter ranges. We can continue as if it was volumes
#         # Salvage the cover from the initial API request, which returned the main cover
#         for relationship in relationships_list:
#             # Search for the dict with pair "type": "author" to make another request to Mangadex for their name
#             if relationship['type'] == 'cover':
#                 cover_id = relationship['id']

#                 cover_request = requests.get(
#                     f"{base_url}/cover/{cover_id}"
#                     )
#                 # Now we have the cover, download it and save it
#                 cover_filename = cover_request.json()['data']['attributes']['fileName']
#                 cover_url = 'https://uploads.mangadex.org/covers/' + us['mdid'] + '/' + cover_filename + '.512.jpg'
#                 cover_file_request = requests.get(cover_url)
#                 with open(os.path.join(workdir, '0001.jpg'), 'wb') as f:
#                     f.write(cover_file_request.content)
#         # Now we have a cover, we can continue as if it was volumes and download the chapters based on Mangadex IDs

# else:
#     # We have volumes, ask user which volumes to download
#     # Now, ask user which volumes to download
#     print('\nVolumes found:')
#     x = 0
#     for volume in pseudo_file_structure[us['clean_title']]:
#         if volume != 'stranded':
#             print(str(x) + ':\t' + volume + ' (' + str(len(pseudo_file_structure[us['clean_title']][volume])) + ' chapters)')
#         else:
#             stranded_chapters = len(pseudo_file_structure[us['clean_title']][volume])
#             if stranded_chapters > 0:
#                 print(str(x) + ':\tStranded Volume' + ' (' + str(stranded_chapters) + ' chapters)')
#             else:
#                 # Don't even print it if there are no chapters in it
#                 pass
#         x += 1

volume_selection = select_volumes_to_download(cr['pseudo_file_structure'])
vs = volume_selection # Shortcut for later
volume_list = vs['volumes_to_download']

    # volumes_to_download = input('Enter the volumes to download, separated by commas: ')
    # if volumes_to_download == 'debug':
    #     print('Entering Debug. Printing useful data...')
    #     pprint(pseudo_file_structure)
    #     print('Exiting Debug')
    #     volumes_to_download = input('Enter the volumes to download, separated by commas (cannot enter DEBUG again): ')
    # volume_list = volumes_to_download.replace(' ', '').split(',')

    # # Before continuing, go straight to the covers:
    # cover_request = requests.get(
    #         f"{base_url}/cover",
    #         params={"manga[]": [us['mdid']], "limit": 100} # Cant order by volume :(
    #         )

    # # Get cover from Mangadex if it's not already there:
    # for volume in volume_list: # Repetitive loop, but avoids doing too many API calls
    #     if not os.path.exists(os.path.join(workdir, volume+'.jpg')): # All covers are jpg
    #         # Get the cover ID from the cover request for this volume if it's available
    #         cover_id = None
    #         for cover in cover_request.json()['data']:
    #             if cover['attributes']['volume'] == str(int(volume)):
    #                 cover_id = cover['id']
    #                 break
    #         if cover_id != None:
    #             # Cover ID found, request the cover
    #             cover_image_request = requests.get(
    #                 f"{base_url}/cover/{cover_id}"
    #                 )
    #             # Now we have the cover, download it and save it
    #             cover_filename = cover_image_request.json()['data']['attributes']['fileName']
    #             cover_url = 'https://uploads.mangadex.org/covers/' + us['mdid'] + '/' + cover_filename + '.512.jpg'
    #             cover_file_request = requests.get(cover_url)
    #             with open(os.path.join(workdir, volume.zfill(4)+'.jpg'), 'wb') as f:
    #                 f.write(cover_file_request.content)

cover_request_and_download(us['mdid'], cr['pseudo_file_structure'], vs['volumes_to_download'])

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

        # Now we can download the images. First, request Mangadex for image data
        chapter_request = requests.get(
            f"{baseUrl}/at-home/server/{chapter_id}"
            )

        # Now we have the image data, we can get the images
        im = 0
        #pprint(chapter_request.json())
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
