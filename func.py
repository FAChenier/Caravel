# This script will handle most complex functions of the main script

import requests
import time
from pprint import pprint
import os

baseUrl = "https://api.mangadex.org"

def contributor_request(contributor_ids: list) -> dict:
    """Takes a list of staff IDs and returns a list of their names in the same order.

    Args:
        contributor_ids (list): list of mangadex staff IDs

    Returns:
        dict: results of the request,
        {
            "names": list of names,
            "duration": time taken to execute the request
        }
    """
    name_list = []
    t1 = time.perf_counter()
    try:
        for author_id in contributor_ids:
            # ! API Request is being made here, this is a marker
            contributor_request = requests.get(
                            f"{baseUrl}/author/{author_id}"
                            )

            name = contributor_request.json()['data']['attributes']['name']
            name_list.append(name) if name not in name_list else None # * Avoid duplication
        t2 = time.perf_counter()
        duration = round(t2 - t1, 2) # Useful later for understanding a rate limiting issue
        # ? Checking time should be done whenever an API request is inside a fast loop
    except:
        # * Likely that authors don't exist or we are rate limited, just skip
        name_list = [""]
        duration = 0
    return {
        "names": name_list,
        "duration": duration
    }


def mangadex_titles_request(title_lookup: str) -> dict:
    """This function will execute the API request for the titles endpoint. It
    will return the response it gets from the API, or any errors received.

    Args:
        title_lookup (str): The title to lookup.

    Returns:
        dict: A dictionary similar to the JSON but in a format that is easier for
        us to use. This will also be cached for a certain amount of time.
        # * Caching is not implemented yet.
    """
    # ! API Request is being made here, this is a marker
    title_request = requests.get(
        f"{baseUrl}/manga",
        params={"title": title_lookup}
    )
    # The title lookup is used for the following in the main script:
    # - Get a list of strings of the titles
    # - Get a list of strings of the IDs
    # - Get a list of anilist links
    # - Get a description for the chosen title (NOT USED?)
    # - Get the year of the chosen title (NOT USED?)
    # - Get the real title of the series (including illegal characters)
    # - Get the author and artist of the series

    title_results = []
    ids_results = []
    anilist_links = []
    real_titles = []
    contributors = [] # * Special format, list of lists. [[author, artist], [author, artist]]. If author and artist are the same, only one is listed.
    cover_ids = []
    mangadex_links = []
    # Loop through the results and append them to the lists as needed:
    for result in title_request.json()["data"]:
        try: # Sometimes the titles are too well classified lmao
            tit = title_results.append(result["attributes"]["title"]["en"])
        except:
            tit = title_results.append(result["attributes"]["title"]["ja-ro"])
        ids_results.append(result["id"])
        real_titles.append(tit)
        cover_ids.append(result["relationships"][2]["id"]) # Experiment, seems that relationships are always ordered...
        mangadex_links.append("https://mangadex.org/title/" + result["id"])

        try: # Not every title has an anilist link, might break when it's not there.
            anilist_links.append("https://anilist.co/manga/" + result["attributes"]["links"]["al"])
        except:
            anilist_links.append("N/A")

        # Get the contributors
        relationships_list = result['relationships']
        # * Experiement: Seems that author/artist are always ordered
        author_id = relationships_list[0]['id']
        artist_id = relationships_list[1]['id']
        authors_list = [author_id] if author_id == artist_id else [author_id, artist_id]
        contributors.append(authors_list)

    return {
        "titles_results": title_results,
        "ids_results": ids_results,
        "mangadex_links": mangadex_links,
        "anilist_links": anilist_links,
        "description": "",  # * Not used yet
        "year": "",         # * Not used yet
        "real_titles": real_titles,
        "contributors": contributors,
        "main_cover_id": cover_ids,
        "result_number": len(title_results),
        "results": title_request.json() # * For debugging
    }


def chapter_request_and_files(mdid: str, series_title: str) -> dict:
    """Execute a mangadex API request for all the chapters in a
    series. Returns a dictionary with the results and other information.

    Args:
        mdid (str): Mangadex ID of the manga to lookup.
        series_title (str): The title of the series.

    Returns:
        dict: See "return" for the format.
    """
    # ! API Request is being made here, this is a marker
    chapter_request = requests.get(
    f"{baseUrl}/manga/{mdid}/feed",
    params={"translatedLanguage[]": "en", "order[chapter]": "asc", "limit": 500}
    )

    #pprint(chapter_request.json())
    # TODO Add a way to offset the request if there are more than 500 chapters
    # TODO Handle error responses

    chapter_id_list = []
    volume_list = []
    # * If we want any other stat, we can add a list that is filled gradually here too

    for chapter in chapter_request.json()["data"]:
        # ? This should exclude "official publisher" chapters
        if chapter["attributes"]["externalUrl"] == None:
            chapter_id_list.append(chapter["id"])
            volume_list.append(chapter["attributes"]["volume"])

# ==============================================================================

    # Build the pseudo file structure right away
    pseudo_file_structure = {series_title: {
        'stranded': {},
    }}

    for chapter in chapter_request.json()["data"]:
        if chapter["attributes"]["externalUrl"] == None:
            chapter_num = chapter["attributes"]["chapter"] # * Will return None if empty, no point try-excepting
            volume_num = chapter["attributes"]["volume"]
            volume_str = str(volume_num).zfill(4) if volume_num is not None else "stranded"

            # If it's stranded, add it to the stranded list. Else, add to its volume dict:
            if volume_str == "stranded":
                pseudo_file_structure[series_title]['stranded'][chapter_num] = chapter["id"]
            else:
                if volume_str not in pseudo_file_structure[series_title]: # Can't create a new dict with an assignment to it
                    pseudo_file_structure[series_title][volume_str] = {}
                pseudo_file_structure[series_title][volume_str][chapter_num] = chapter["id"]
    # By the end of this loop, the pseudo file structure should be complete

    # Check if everything ended up in stranded. If so, use chapter ranges instead:
    if len(pseudo_file_structure[series_title]['stranded']) == len(chapter_id_list):
        # Default to chapter ranges of 10, may be changed in settings later.
        # * The setting is not implemented yet
        # If there's not enoug chapters to fill the last range, put in stranded. Can apply to the first volume:
        pseudo_file_structure = {series_title: {
            'stranded': {},
        }}
        for i in range(0, len(chapter_id_list), 10):
            volume_str = str(i // 10).zfill(4)
            pseudo_file_structure[series_title][volume_str] = {}
            for j in range(i, i+10):
                try:
                    pseudo_file_structure[series_title][volume_str][chapter_id_list[j]] = chapter_id_list[j]
                except:
                    pseudo_file_structure[series_title]['stranded'][chapter_id_list[j]] = chapter_id_list[j]
        # * The above is completely untested. It's just a concept for now.
    # Rebuild the volume list
    volume_list = list(pseudo_file_structure[series_title].keys())

# ==============================================================================

    #pprint(pseudo_file_structure)

    return {
        "chapter_id_list": chapter_id_list,
        "volumes": volume_list,
        "chapter_number": len(chapter_id_list),
        "pseudo_file_structure": pseudo_file_structure,
        "results": chapter_request.json()
    }


def build_folders(pseudo_file_structure: dict) -> None:
    """Builds the folders from a pseudo file structure. Returns a dictionary
    of the outcomes.

    Args:
        pseudo_file_structure (dict): A pseudo file structure built by a previous function.
    """
    # First, build the root folder named after the series in the current directory:
    root_folder = os.path.join(os.getcwd(), "books", list(pseudo_file_structure.keys())[0])
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)
    # Now, create a folder for each volume:
    for volume in pseudo_file_structure[list(pseudo_file_structure.keys())[0]]:
        volume_folder = os.path.join(root_folder, volume)
        if not os.path.exists(volume_folder):
            os.makedirs(volume_folder)



def select_volumes_to_download(pseudo_file_structure: dict) -> dict:
    """Takes a pseudo file structure and displays its content and asks
    the user which volumes within it to download.

    Args:
        pseudo_file_structure (dict): a pseudo file structure built by a previous function

    Returns:
        dict: See returned structure for more information.
    """
    # List all volumes available, and how many chapters are in each:
    print("Available volumes:")
    i = 0
    for volume in pseudo_file_structure[list(pseudo_file_structure.keys())[0]]:
        print(f"{i}: \t {volume} ({len(pseudo_file_structure[list(pseudo_file_structure.keys())[0]][volume])} chapters)")
        i += 1
    # Ask the user which volumes to download:
    user_input = input("Enter the numbers of the volumes you want to download, separated by commas, or a range ('1-5'): ")
    # Parse the user input and build a list of volumes to download, which are inherently their IDs:
    volumes_to_download = []
    for volume in user_input.split(","):
        if "-" in volume:
            # It's a range, so add all the volumes in the range:
            volume_range = volume.split("-")
            for i in range(int(volume_range[0]), int(volume_range[1])+1):
                volumes_to_download.append(i)
        else:
            # It's a single volume, so add it to the list:
            volumes_to_download.append(int(volume)) # ! This has no error handling!
    return {
        "volumes_to_download": volumes_to_download
    }


def cover_request_and_download(mdid, pseudo_file_structure, volumes_to_download):
    """Requests the cover for the volumes and downloads it to the root folder.

    Args:
        mdid (str): Mangadex ID of the manga to lookup.
        pseudo_file_structure (dict): A pseudo file structure built by a previous function.
        volumes_to_download (list): A list of volumes to download.
    """
    # ! API Request is being made here, this is a marker
    cover_request = requests.get(
            f"{baseUrl}/cover",
            params={"manga[]": [mdid], "limit": 100} # Cant order by volume :(
            )

    # Loop through each volume to download, check if the cover already exists, and if not, download it:
    try:
        for volume in volumes_to_download:
            cover_path = os.path.join(os.getcwd(), "books", list(pseudo_file_structure.keys())[0], str(volume).zfill(4) + ".jpg")
            if not os.path.exists(cover_path):
                # Download the cover, check if there's a cover in cover_request for this volume:
                cover_id = None
                for cover in cover_request.json()['data']:
                    if int(cover['attributes']['volume']) == volume:
                        # Found the cover
                        cover_id = cover['id']
                        break
                if cover_id is not None:
                    cover_image_request = requests.get(
                        f"{baseUrl}/cover/{cover_id}"
                        )
                    # Now we have the cover, download it and save it
                    cover_filename = cover_image_request.json()['data']['attributes']['fileName']
                    cover_url = 'https://uploads.mangadex.org/covers/' + mdid + '/' + cover_filename + '.512.jpg'
                    cover_file_request = requests.get(cover_url)
                    with open(cover_path, 'wb') as f:
                        f.write(cover_file_request.content)
                # Check if no covers were found, if so, download the default cover:
                # ! This is not implemented yet
            else:
                # Cover already exists, do nothing:
                pass
    except:
        print("Failed cover request, response gotten from the server:")
        pprint(cover_request.json())
        pass