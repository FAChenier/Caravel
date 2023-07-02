# Miscellaneous functions for the project

import requests

# From https://stackoverflow.com/a/34325723
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)

    Start by calling with "iteration" = 0, then loop and call again to update the current iteration (basically the progress towards "total")
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

# Function for downloading individual images for chapters:
def download_chapter_image(baseUrl, chapter_hash, image, image_path):
    # Build the URL to the image, download it, then save it.
    im_url = baseUrl + '/data/' + chapter_hash + '/' + image                        # Build the URL to the image
    image_request = requests.get(im_url)                                         # Get the downloaded image extension
    with open(image_path+'.png', 'wb') as f: # Save the image
        f.write(image_request.content)

