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

import requests
from pprint import pprint
import os
from misc_utils import printProgressBar
from kcc_conversion import img_dir_to_epub as kcc_convert
from push_to_calibre import push_to_calibre as calibre_push

title = input('Enter the title of the manga: ')
base_url = "https://api.mangadex.org"

title_lookup = requests.get(
    f"{base_url}/manga",
    params={"title": title}
)

title_list = [manga['attributes']['title']['en'].strip() for manga in title_lookup.json()["data"]]
id_list = [manga['id'] for manga in title_lookup.json()["data"]]
try:
    al_link_list = ["https://anilist.co/manga/" + manga['attributes']['links']['al'] for manga in title_lookup.json()["data"]]
except:
    # AL links are not always present
    al_link_list = ["No Anilist Link" for manga in title_lookup.json()["data"]]

# This block is to confirm the manga to use
if len(title_list) > 1:
    print('Multiple results found:')
    i = 0
    for manga_title in title_list:
        # Print a useful list of results and ask which one is correct
        print(str(i+1) + ":\t" + " (" + al_link_list[i] +  ")\t" + title_list[i])
        i += 1
    id_to_use = int(input('\nID of manga to use: ')) - 1
elif len(title_list) == 0:
    # No results found
    print('No results found, exiting')
    exit()
else:
    # Ensure the unique result is correct
    print('Single result found:')
    print(title_list[0] + " (" + al_link_list[0] + ")")
    make_sure = input('Is this the correct manga? (y/n): ')
    if make_sure == 'y':
        id_to_use = 0
    else:
        exit()
# TODO: Make this a loop so that it keeps asking until it has a valid result to use or user exits

mdid = id_list[id_to_use] # mdid is the MangaDex ID of the manga to use
# Now we might as well collect as much metadata as we can right now
meta_desc = title_lookup.json()["data"][id_to_use]['attributes']['description']['en']
meta_year = int(title_lookup.json()["data"][id_to_use]['attributes']['year'])
meta_title = title_lookup.json()["data"][id_to_use]['attributes']['title']['en']

relationships_list = title_lookup.json()["data"][id_to_use]['relationships']
authors_list = []
for relationship in relationships_list:
    # Search for the dict with pair "type": "author" to make another request to Mangadex for their name
    if relationship['type'] == 'author' or relationship['type'] == 'artist':
        author_id = relationship['id']
        author_request = requests.get(
            f"{base_url}/author/{author_id}"
            )
        name = author_request.json()['data']['attributes']['name']
        authors_list.append(name) if name not in authors_list else None

# ====================================================================================================
# Now we go get the images
# First, create a working directory in this current directory
# Some manga have special characters that are not allowed in folder names, like ? or !. We need to remove them
clean_title = title_list[id_to_use].replace('?', '').replace('!', '').replace(':', '').replace('/', '').replace('\\', '').replace('*', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '') # Brute force, but it works

# Check if \books exists, if not, create it
if not os.path.exists(os.path.join(os.getcwd(), 'books')):
    os.mkdir(os.path.join(os.getcwd(), 'books'))

workdir = os.path.join(os.getcwd() + "\\books", clean_title)
if os.path.exists(workdir):
    # Before trying, check if it already exists
    print('Folder already exists, continuing')
else:
    print('Creating folder')
    workdir = os.path.join(workdir)
    os.mkdir(workdir)
    # This creates a folder in which we can place volumes. At this time, we don't know if the manga has volumes. We will assume volumes are specified for now

# sending a GET manga feed request will return a list of chapter objects, with IDs but most importantly the volume number, if available
# We request only english chapters, and sort them by chapter number so that we don't need to do it ourselves. We also request 500 chapters at a time, which should be enough for most manga. I don't read One Piece
chapter_request = requests.get(
    f"{base_url}/manga/{mdid}/feed",
    params={"translatedLanguage[]": "en", "order[chapter]": "asc", "limit": 500}
    )
# TODO: Add a way to detect if there are more than 500 chapters and do another request with an offset if it does

# FIXME: We don't know if there are duplicate chapters! If so, we need to determine which to use. Likely going to be done based on scanlation group
# TODO: Warn if some chapters are not in volumes
chapter_id_list = [chapter['id'] for chapter in chapter_request.json()["data"]]

# To simplify the way we understand the file structure, we use a dictionary that represents it.
# When it's built, it will represent the potential file structure. We can then locate chapters without executing
# any additional requests to mangadex and hence reduce the load we are applying, even if marginal
# Note: "stranded" is a folder that will contain chapters that are not in a volume. FIXME if we find a manga that doesn't use volumes
pseudo_file_structure = {clean_title: {
    'stranded': {},
}}

# Go through all chapter object and keep the ones we want. Build a file structure as we go
for chapter in chapter_request.json()["data"]:
    try:
        work_chapter = chapter['attributes']['chapter']
    except:
        work_chapter = "No Chapter"

    try:
        work_volume = chapter['attributes']['volume']
        text_volume = str(work_volume).zfill(4)
    except:
        work_volume = None
        text_volume = 'Stranded'


    # Check volume. If none, place in "stranded" folder. If volume, place in volume folder named simply "0001" where 1 is volume number. 10 is 0010 and so on
    if work_volume == None:
        # place in stranded folder, check if it already exists. If not, create it
        stranded_path = os.path.join(workdir, 'stranded')
        if not os.path.exists(stranded_path):
            os.mkdir(stranded_path)
        # Now we have a stranded folder, place the chapter in it
        pseudo_file_structure[clean_title]['stranded'][work_chapter] = chapter['id']
        # This creates a pair inside the pseudo folder "stranded" such that: {chapter number: chapter ID} so we can easily find it later
    else:
        # Chapter has a volume, create a volume folder in workdir and pseudo_file_structure using volume number format above
        volume_path = os.path.join(workdir, text_volume)
        if not os.path.exists(volume_path):
            os.mkdir(volume_path)
        # Now we have a volume folder, place the chapter in it
        # If volume not in the pseudo_file_structure, create it
        if text_volume not in pseudo_file_structure[clean_title]:
            pseudo_file_structure[clean_title][text_volume] = {}
        pseudo_file_structure[clean_title][text_volume][work_chapter] = chapter['id']
# We should now have a map of where things belong

# Now, ask user which volumes to download
print('\nVolumes found:')
x = 0
for volume in pseudo_file_structure[clean_title]:
    if volume != 'stranded':
        print(str(x) + ':\t' + volume)
    else:
        print(str(x) + ':\tStranded Volume')
    x += 1

volumes_to_download = input('Enter the volumes to download, separated by commas: ')
if volumes_to_download == 'debug':
    print('Entering Debug. Printing useful data...')
    pprint(pseudo_file_structure)
    print('Exiting Debug')
    volumes_to_download = input('Enter the volumes to download, separated by commas (cannot enter DEBUG again): ')
volume_list = volumes_to_download.replace(' ', '').split(',')

# Before continuing, go straight to the covers:
cover_request = requests.get(
        f"{base_url}/cover",
        params={"manga[]": [mdid], "limit": 100} # Cant order by volume :(
        )

# Get cover from Mangadex if it's not already there:
for volume in volume_list: # Repetitive loop, but avoids doing too many API calls
    if not os.path.exists(os.path.join(workdir, volume+'.jpg')): # All covers are jpg
        # Get the cover ID from the cover request for this volume if it's available
        cover_id = None
        for cover in cover_request.json()['data']:
            if cover['attributes']['volume'] == str(int(volume)):
                cover_id = cover['id']
                break
        if cover_id != None:
            # Cover ID found, request the cover
            cover_image_request = requests.get(
                f"{base_url}/cover/{cover_id}"
                )
            # Now we have the cover, download it and save it
            cover_filename = cover_image_request.json()['data']['attributes']['fileName']
            cover_url = 'https://uploads.mangadex.org/covers/' + mdid + '/' + cover_filename + '.512.jpg'
            cover_file_request = requests.get(cover_url)
            with open(os.path.join(workdir, volume.zfill(4)+'.jpg'), 'wb') as f:
                f.write(cover_file_request.content)

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
    volume = volume.zfill(4)
    vol_path = os.path.join(workdir, volume)
    if not os.path.exists(vol_path):
        os.mkdir(vol_path)

    # Create each chapters inside the volume folder. A chapter is a folder in which we'll put the images. Name it the same is pseudo_file_structure
    chaps = 0
    for chapter in pseudo_file_structure[clean_title][volume]:
        chaps += 1
        print('Starting Chapter ' + str(chaps) + " of " + str(len(pseudo_file_structure[clean_title][volume])))
        ch_path = os.path.join(workdir, volume, chapter)
        if not os.path.exists(os.path.join(workdir, volume, chapter)):
            os.mkdir(os.path.join(workdir, volume, chapter))
        # Now we have a chapter folde, we need to get the chapter ID from pseudo_file_structure
        chapter_id = pseudo_file_structure[clean_title][volume][chapter]

        # Now we can download the images. First, request Mangadex for image data
        chapter_request = requests.get(
            f"{base_url}/at-home/server/{chapter_id}"
            )

        # Now we have the image data, we can get the images
        im = 0
        total_images = len(chapter_request.json()['chapter']['data'])
        baseUrl = chapter_request.json()['baseUrl']
        chapter_hash = chapter_request.json()['chapter']['hash']

        print(
            '========================================',
            'Downloading ' + str(total_images) + ' Images', sep='\n'
            )

        for image in chapter_request.json()['chapter']['data']:
            printProgressBar(im, total_images, prefix = 'Progress:', suffix = 'Complete', length = 50)
            im+=1
            # Check if the image already exists. If so, skip it. If first image, ask if we should overwrite (TODO)
            if os.path.exists(os.path.join(workdir, volume, chapter, str(im).zfill(5))+".png") or os.path.exists(os.path.join(workdir, volume, chapter, str(im).zfill(5))+".jpg"):
                # Image already exists, skip it
                continue
            else:
                # Build the URL to the image, download it, then save it.
                im_url = baseUrl + '/data/' + chapter_hash + '/' + image                        # Build the URL to the image
                image_request = requests.get(im_url)                                            # Request the image
                image_extension = image.split('.')[-1]                                          # Get the downloaded image extension
                with open(os.path.join(workdir, volume, chapter, str(im).zfill(5))+'.png', 'wb') as f: # Save the image
                    f.write(image_request.content)

                # TODO: Mangadex expects a PUSH to report if the provided link was good or not. Do when possible

                # Last, rename the image to something simple to avoid breaking the filesystem, use 00001, 00002, etc should be enough
                #os.rename(os.path.join(workdir, volume, chapter, image), os.path.join(workdir, volume, chapter, str(im).zfill(5) + '.' + image_extension))

        # All images downloaded, go to next chapter
        printProgressBar(total_images, total_images, prefix = 'Progress:', suffix = 'Complete', length = 50) # Ducktape fix to make sure the progress bar is full lol
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
            title_list[id_to_use],
            volume,
            'Vol. '+ str(volume) + ' - ' + meta_title,
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
