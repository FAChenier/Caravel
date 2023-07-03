# This script holds navigation functions to be called in a main script.

import time
from misc_utils import *
from func import *

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
        if inpt == ("back" or "exit"):
            response_type = "nav"
        else:
            response_type = "title"

    except KeyboardInterrupt:
        response_type = "invalid_input"
        inpt = "exit"
        error = "KeyboardInterrupt"
    except Exception as e:
        response_type = "invalid_input"
        inpt = "error"
        error = "CATASTROPHIC ERROR:\n" + str(e)

    # Return the title
    return {
        "response_type": response_type,
        "response": inpt,
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

    user_input = input("Enter a number to select a title (can also \"back\" or \"exit\"): ")

    if user_input == "back":
        # * User wants to go back
        response_type = "nav"
        mdid = ""
        title = ""
        contributors = ""
        clean_title = ""
    elif user_input == "exit":
        # * User wants to exit
        response_type = "nav"
        mdid = ""
        title = ""
        contributors = ""
        clean_title = ""
    elif user_input.isnumeric():
        user_input = int(user_input)
        if user_input > results['result_number'] or user_input < 1:
            # ? Input is numeric, but out of range
            response_type = "invalid_input"
            mdid = ""
            title = ""
            contributors = ""
            clean_title = ""
        else:
            # * Input is numeric and in range, valid selection!
            response_type = "title_selection"
            mdid = results['ids_results'][int(user_input)-1]
            title = results['titles_results'][int(user_input)-1]
            contributors = results['contributors'][int(user_input)-1][0]
            clean_title = title.replace(":", "").replace("/", "").replace("\\", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")
    else:
        # ! Invalid input, dunno why
        response_type = "invalid_input"
        mdid = ""
        title = ""
        contributors = ""
        clean_title = ""
    # else:
    #     try:
    #         response_type = "title_selection"
    #         mdid = results['ids_results'][int(user_input)-1]
    #         title = results['titles_results'][int(user_input)-1]
    #         contributors = results['contributors'][int(user_input)-1][0]
    #         clean_title = title.replace(":", "").replace("/", "").replace("\\", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")
    #     except:
    #         # Invalid input
    #         response_type = "invalid_input"
    #         mdid = ""
    #         title = ""
    #         contributors = ""
    #         clean_title = ""

    return {
        "response_type": response_type,
        "response": user_input,
        "mdid": mdid,
        "series_title": title,
        "clean_title": clean_title,
        "contributors": contributors
    }


def title_search_nav() -> dict:
    """Requests the user enters a title to search for, then handles navigation
    # ! This function will make an API request through mangadex_titles_request()
    Returns the result of the API request

    Returns:
        dict: Results of the API request
    """
    # Get the title to search for
    user_search = "none!"
    while user_search == "none!":
        user_search = title_search()
        # Check if the user wants to navigate
        if user_search['response_type'] == 'nav':
            if user_search['response'] == 'back':
                # Request title again?
                print('\n\nGoing back...\n\n')
                user_search = "none!"
            elif user_search['response'] == 'exit':
                print('\n\nExiting...\n\n')
                exit()
            else:
                # * Should never get here
                print('\n\nInvalid input, please try again\n')
                user_search = "none!"
        # Check if the user entered a title
        elif user_search['response_type'] == 'title':
            # We can assume this is a valid result since the function handles checking that:
            user_search = user_search['response']
        elif user_search["response_type"] == "invalid_input":
            print('\n\nInvalid input, please try again\n')
            user_search = "none!"
    # We should now have a valid title to lookup
    title_lookup = mangadex_titles_request(user_search)
    # TODO in the future, if this returns an empty list, ask the title again
    # Return the results
    return title_lookup


# Series selection screen
def series_select_nav(title_lookup: dict) -> dict:
    """Displays a menu and handles navigation for series selection screen. Self-contained including the return to
    the title lookup screen.

    Args:
        title_lookup (dict): The output of the function mangadex_titles_request().

    Returns:
        dict: See returned value for structure.
    """
    user_select = 'none'
    while user_select == 'none':
        user_select = display_results(title_lookup)
        # Use the full display_results response to narrow down what to do next:
        if user_select['response_type'] == 'nav':
            # Nav handler not implemented yet so we do our best:
            if user_select['response'] == 'back':
                print('\n\nGoing back...\n\n')
                title_lookup = title_search_nav()
                user_select = 'none'
            elif user_select['response'] == 'exit':
                print('\n\nExiting...\n\n')
                exit()
            else:
                # * Should never get here
                print('\n\nInvalid input, please try again\n')
                user_select = 'none'
        elif user_select['response_type'] == 'title_selection':
            # We can assume this is a valid result since the function handles checking that:
            #user_select = int(user_select['response'])
            continue
        elif user_select["response_type"] == "invalid_input":
            print('\n\nInvalid input, please try again\n')
            user_select = 'none'
    # We should now have a valid selection
    return user_select