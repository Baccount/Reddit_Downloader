import concurrent.futures as futures
import configparser
import os
import re
from time import sleep

import praw
import requests

from tools import argument, blue, green, red, show_splash, options

VERSION = "0.1"


class R3dditScrapper:
    def __init__(
        self,
        sub="pics",
        limit=1,
        order="hot",
        nsfw="True",
        argument=False,
        path=None,
        test=False,
    ):
        """
        It downloads images from a subreddit, and saves them to a folder
        :param sub: The subreddit you want to download from
        :param limit: The number of images to download
        :param order: hot, top, new
        :param nsfw: If you want to download NSFW images, set this to True, defaults to False (optional)
        :param argument: If you want to use the arguments from the command line, set this to True, defaults to False (optional)
        :param folder: The path you want to save to, defaults to the subreddit name (optional)
        """

        config = configparser.ConfigParser()
        config.read("config.ini")
        self.test = test
        self.sub = sub
        self.limit = limit
        self.order = order
        self.argument = argument
        self.path = f"images/{self.sub}/" if not path else f"{path}/{self.sub}/"
        client_id = config["Reddit"]["client_id"]
        client_secret = config["Reddit"]["client_secret"]
        user_agent = (
            "R3dditScrapper / https://github.com/Baccount/Reddit_Downloader/tree/master"
        )
        self.nsfw = nsfw
        if self.nsfw.lower() == "true" or self.nsfw.lower() == "t":
            self.nsfw = True
        else:
            self.nsfw = False
        self.reddit = praw.Reddit(
            client_id=client_id, client_secret=client_secret, user_agent=user_agent
        )

    def download(self, image):
        try:
            r = requests.get(image["url"])
            with open(image["fname"], "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(e)

    def set_order(self):
        """Set the order of the images to download"""
        if self.order == "hot":
            return self.reddit.subreddit(self.sub).hot(limit=None)
        elif self.order == "top":
            return self.reddit.subreddit(self.sub).top(limit=None)
        elif self.order == "new":
            return self.reddit.subreddit(self.sub).new(limit=None)

    def get_images(self) -> list:
        """Get the images from the subreddit"""
        images = []
        try:
            go = 0
            submissions = self.set_order()
            for submission in submissions:
                if (
                    not submission.stickied
                    and submission.over_18 == self.nsfw
                    and submission.url.endswith(("jpg", "jpeg", "png", "gif"))
                ):
                    fname = self.path + re.search(
                        r"(?s:.*)\w/(.*)",
                        submission.url,
                    ).group(1)
                    if not os.path.isfile(fname):
                        # Add image Only if it does not already exist
                        images.append({"url": submission.url, "fname": fname})
                        go += 1
                        print(green(f"{go}/{self.limit}"))
                        if go >= self.limit:
                            break
            self.make_dir(images)
            return images
        # catch bad request errors
        except Exception as e:
            print(red(str(e)))
            print(red("Subreddit not found"))
            # restart program if error occurs
            input("Press enter to continue: ")
            main()

    def make_dir(self, images):
        if len(images):
            if not os.path.exists(self.path):
                os.makedirs(self.path)

    def start(self):
        print(blue("Downloading images from r/" + self.sub))
        with futures.ThreadPoolExecutor() as executor:
            executor.map(self.download, self.get_images())
        print(green("Saved images to " + self.path))
        input("Press enter to continue: ")
        if self.argument and not self.test:
            # exit after using terminal arguments
            exit(0)
        elif self.test:
            # for pytest
            return None
        else:
            # restart the program if not using terminal arguments
            main()


def create_config():
    """Create config file if it doesn't exist"""
    if not os.path.isfile("config.ini"):
        config = configparser.ConfigParser()
        config.add_section("Reddit")
        config.set("Reddit", "client_id", input("Enter your client_id: "))
        config.set("Reddit", "client_secret", input("Enter your client_secret: "))
        with open("config.ini", "w") as f:
            config.write(f)


def setPath():
    """Set the path to download to"""
    config = configparser.ConfigParser()
    config.read("config.ini")
    # if path exists, use it
    if not config["Path"]["path"]:
        config.add_section("Path")
    config.set("Path", "path", input("Enter the path to download to: "))
    # check if the path exists
    # try to create the path if it doesn't exist
    if not os.path.exists(config["Path"]["path"]):
        try:
            os.makedirs(config["Path"]["path"])
        # catch incorrect path error
        except Exception as e:
            print(e)
            setPath()
    with open("config.ini", "w") as f:
        config.write(f)


def getInput():
    sub, limit, order, path = "", 0, "hot", ""
    sub = input("Enter subreddit, " + " " * 20 + red("O :Options\n") + ": ")
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
    return sub, limit, order, path

def main():
    create_config()
    argument()
    show_splash()
    sub, limit, order, path = getInput()
    config = configparser.ConfigParser()
    config.read("config.ini")
    if "Path" in config:
        path = config["Path"]["path"]
        R3dditScrapper(sub, limit, order, path=path).start()
    else:
        R3dditScrapper(sub, limit, order).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(1)
