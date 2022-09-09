import argparse as ap
import configparser
import os
import sys

import praw
from prawcore.exceptions import ResponseException
from pyfiglet import Figlet


def blue(text: str) -> str:
    """
    `blue` takes a string and returns a blue string
    """
    return "\033[34m" + text + "\033[0m"


def green(text: str) -> str:
    """
    `green` takes a string and returns a green string
    """
    return "\033[32m" + text + "\033[0m"


def red(text: str) -> str:
    """
    `red` takes a string and returns a red string
    """
    return "\033[31m" + text + "\033[0m"


def clear_screen():
    """
    It prints 25 new lines
    """
    print("\n" * 25)


def showSplash():
    """
    Display splash screen
    """

    clear_screen()
    title = "R3ddit\n Scrapper"
    f = Figlet(font="standard")
    print(blue(f.renderText(title)))


def argument():
    """
    Parsing the arguments passed by the user.
    optional arguments:
    -s --sub: The subreddit you want to download from
    -l --limit: number of images to download
    -o --order: hot, top, new
    -n --nsfw: False = NO NSFW images
    -p --path: The path you want to save to
    """
    parser = ap.ArgumentParser(description="R3ddit Scrapper")
    parser.add_argument(
        "-s", "--sub", help="The subreddit you want to download from", required=False
    )
    parser.add_argument(
        "-l", "--limit", help="The number of images to download", required=False
    )
    parser.add_argument("-o", "--order", help="hot, top, new", required=False)
    parser.add_argument(
        "-n",
        "--nsfw",
        help="Set to False of you want to download all NON NSFW images",
        required=False,
    )
    parser.add_argument(
        "-p", "--path", nargs="+", help="The folder you want to save to", required=False
    )
    # if no arguments are passed, return
    if len(sys.argv) == 1:
        return
    sort = ["hot", "top", "new"]
    sub = parser.parse_args().sub if parser.parse_args().sub else "pics"
    limit = int(parser.parse_args().limit) if parser.parse_args().limit else 1
    order = parser.parse_args().order if parser.parse_args().order in sort else "hot"
    nsfw = parser.parse_args().nsfw if parser.parse_args().nsfw else "True"
    path = parser.parse_args().path if parser.parse_args().path else None
    # join path with space fix https://stackoverflow.com/a/26990349
    path = " ".join(path) if path else None
    print(f"Subreddit: {sub}")
    print(f"Limit: {limit}")
    print(f"Order: {order}")
    print(f"NSFW: {nsfw}")
    print(f"Path: {path if path else 'Local directory'}")
    from main import R3dditScrapper

    R3dditScrapper(
        sub=sub, limit=limit, order=order, nsfw=nsfw, argument=True, path=path
    ).start()


def check_update(testing=False) -> bool:
    # download latest version asynchronously
    """
    Check if there is a new version of the program
    """
    # download async the version file
    try:
        import requests

        from main import VERSION

        r = requests.get(
            "https://raw.githubusercontent.com/Baccount/Reddit_Downloader/master/version.txt"
        )
        r = r.text.strip()
        if not r == VERSION:
            print(" " * 45 + red(VERSION))
            print(f"There is a new version of the program: {r}")
            print(blue("https://github.com/Baccount/Reddit_Downloader"))
            input("Press Enter to continue: ")
            return True
        else:
            print(green(f"Currently running the latest version {red(VERSION)}"))
            if not testing:
                input("Press Enter to continue: ")
            return True
    # trunk-ignore(flake8/E722)
    except:
        print("Could not check for updates")
        return False


def options():
    from main import VERSION, main
    while True:
        clear_screen()
        # print the options
        print(blue(f"\nOptions:           {red('V. ')}{red(VERSION)}\n"))
        option = input(
            "S: Set path\nV: View current path \nC: Check for updates\nN: NSFW\nR: Reset All Settings\nQ: Quit\n: "
        )
        if option.lower() == "s":
            setPath()
        elif option.lower() == "v":
            config = configparser.ConfigParser()
            config.read("config.ini")
            if config.has_section("Path"):
                print(green(config["Path"]["path"]))
                input("Press Enter to continue: ")
            else:
                print(red("No path set"))
        elif option.lower() == "c":
            check_update()
        elif option.lower() == "r":
            reset()
        elif option.lower() == "n":
            nsfw()
        elif option.lower() == "q":
            break
    main(skip=True)

def nsfw():
    """_summary_
    Enable or disable NSFW images
    NSFW is enabled by default
    """
    clear_screen()
    config = configparser.ConfigParser()
    config.read("config.ini")
    if not config.has_section(section="NSFW"):
        config.add_section("NSFW")
    else:
        print("NSFW is currently: " + green(config.get("NSFW", "nsfw")))
    choice = input("NSFW (y/n): ")
    if choice.lower() == "y":
        config.set("NSFW", "nsfw", "True")
        clear_screen()
        print(green("NSFW Enabled"))
    elif choice.lower() == "n":
        config.set("NSFW", "nsfw", "False")
        clear_screen()
        print(green(green("NSFW Disabled")))
    # save the config
    with open("config.ini", "w") as f:
        config.write(f)
    input("Press Enter to continue: ")
    return

def reset():
    """
    Reset all settings
    """
    choice = input("Are you sure you want to reset all settings? (y/n): ")
    if choice.lower() == "y":
        try:
            os.remove("config.ini")
            print(green("Settings reset"))
        except FileNotFoundError:
            print(red("Could not reset settings"))


def verifyReddit(client_id, client_secret) -> bool:
    """Verify the reddit credentials"""
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=(
            "R3dditScrapper / https://github.com/Baccount/Reddit_Downloader/tree/master"
        ),
    )
    try:
        reddit.auth.scopes()
        return True
    except ResponseException:
        return False


def create_config():
    """Create config file if it doesn't exist"""
    if not os.path.isfile("config.ini"):
        config = configparser.ConfigParser()
        config.add_section("Reddit")
        client_id = input("Enter your client_id: ")
        config.set("Reddit", "client_id", client_id)
        client_secret = input("Enter your client_secret: ")
        config.set("Reddit", "client_secret", client_secret)
        with open("config.ini", "w") as f:
            config.write(f)
        if not verifyReddit(client_id, client_secret):
            # credentials are invalid
            print(red("Invalid credentials"))
            os.remove("config.ini")
            create_config()


def setPath():
    clear_screen()
    config = configparser.ConfigParser()
    config.read("config.ini")
    print(blue("Enter the path you want to save to" + 20 * " " + red("R: Reset path\n")))
    print("1: Downloads")
    print("2: Documents")
    print("3: Desktop")
    print("Q: Quit")
    path = input("Enter the path to download to: ")
    """Set the path to download to"""
    if path.lower() == "r":
        resetPath()
        return
    elif path == "1":
        # set download path to download folder
        path = os.path.join(os.path.expanduser("~"), "Downloads")
    elif path == "2":
        # set download path to documents folder
        path = os.path.join(os.path.expanduser("~"), "Documents")
    elif path == "3":
        # set download path to desktop folder
        path = os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() == "q":
        return
    savePath(path)
    return

def resetPath():
    """Reset the path to download to"""
    config = configparser.ConfigParser()
    config.read("config.ini")
    if config.has_section("Path"):
        config.remove_section("Path")
        with open("config.ini", "w") as f:
            config.write(f)
        print(green("Path has been reset"))
        input("Press Enter to continue: ")

def savePath(path):
    config = configparser.ConfigParser()
    config.read("config.ini")
    # if path exists, use it
    if not config.has_section(section="Path"):
        config.add_section("Path")
    config.set("Path", "path", path)
    # check if path exists
    if not os.path.exists(config["Path"]["path"]):
        print(red("Path does not exist"))
        # call setPath again
        setPath()
    with open("config.ini", "w") as f:
        config.write(f)

def getInput() -> str:
    sub, limit, order, nsfw = "", 0, "hot", "True"
    # read config file
    config = configparser.ConfigParser()
    config.read("config.ini")
    if config.has_section("NSFW"):
        nsfw = config.get("NSFW", "nsfw")
    sub = input(
        "Enter subreddit "
        + " " * 20
        + green("O :Options  ")
        + green("Q :Quit\n")
        + ": "
    )
    if sub.lower() == "o":
        options()
    if sub.lower() == "q":
        exit(0)
    if not sub:
        sub = "pics"
    try:
        limit = int(input("Number of photos: "))
    except ValueError:
        print(red("This is not a number, defaulting to 1"))
        limit = 1
    order = input("Order (hot, top, new): ")
    if order.lower() == "o":
        options()
    if order.lower() not in ["hot", "top", "new"]:
        print(red("Defaulting to hot"))
        order = "hot"
    return sub, limit, order, nsfw
