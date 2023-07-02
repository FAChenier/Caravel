# This script holds navigation functions to be called in a main script.

import time
from misc_utils import *

# Title search function
def title_search() -> dict:
    """This function will load a new CLI "pane" that asks the user for a title to
    lookup. The function doesn't do any API request, it only returns the title
    and allows for some navigation.

    Returns:
        dict: Returns a dictionary with results, similar to a JSON response:
        {
            "lookup": "Title",
            "nav": "any navigation input, like "back" or "exit"",
            "error": "any error that might have occured"
        }
    """
    # Clear the screen
    # clear_screen()
    # Ask for the title
    error = ""
    try:
        inpt = input("Enter a title to search for: ")
        if inpt == "back":
            nav = "back"
        elif inpt == "exit":
            nav = "exit"
        else:
            nav = "none"
            title = inpt
    except KeyboardInterrupt:
        nav = "exit"
        title = ""
    except Exception as e:
        nav = "error"
        title = ""
        error = "CATASTROPHIC ERROR:\n" + str(e)

    # Return the title
    return {
        "lookup": title,
        "nav": nav,
        "error": error
        }

def nav_handler(navigation_input: str, previous_func) -> None:
    """This function will handle navigation input from the user. It will take
    navigation_input and will handle it accordingly. This should be called
    any time a navigation request is received. Valid requests are describred
    below.

    Args:
        navigation_input (str): The string representing a navigation request.
        Valid requests are:
            "back": Go back one step in the navigation.
            "exit": Exit the program.
            "none": Do nothing.
        previous_func (function): The function that was previously called.
        # ! This won't work right now, needs some wucky stuff with kwargs?
    """
    # Handle the navigation input
    if navigation_input == "back":
        # Go back one step in the navigation
        print("Going back...")
        time.sleep(3)
        previous_func()
    elif navigation_input == "exit":
        # Exit the program
        print("Exiting...")
        time.sleep(1)
        exit()
    elif navigation_input == "none":
        # Do nothing
        pass
    else:
        # Do nothing
        pass

# Display search results
def display_results(results: dict) -> dict:
    """This function will display the results of a title search. It will take
    a dictionary of results and display them to the user.

    results should be in the following format:
    {
        "titles_results": list of titles,
        "ids_results": list of ids,
        "mangadex_links": list of mangadex links,
        "result_number": number of results,
    }

    Args:
        results (dict): A dictionary of results from a title search.

    Returns:
        dict: Returns a dictionary with results, similar to a JSON response.
    """
    # Clear the screen
    # clear_screen()

    # Display the results
    print(f"Found {results['result_number']} results:")
    for i in range(results['result_number']):
        print(f"{i+1}: {link(results['mangadex_links'][i], results['titles_results'][i])}")
    user_input = input("Enter a number to select a title, or enter \"back\" to go back: ")
    if user_input == "back":
        response_type = "nav"
        mdid = ""
        title = ""
        contributors = ""
        clean_title = ""
    else:
        response_type = "title_selection"
        mdid = results['ids_results'][int(user_input)-1]
        title = results['titles_results'][int(user_input)-1]
        contributors = results['contributors'][int(user_input)-1][0]
        clean_title = title.replace(":", "").replace("/", "").replace("\\", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")

    return {
        "response_type": response_type,
        "response": user_input,
        "mdid": mdid,
        "series_title": title,
        "clean_title": clean_title,
        "contributors": contributors
    }