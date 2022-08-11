from config import Config
from twitter_scraper import TwitterScraper

def main ():
    # Get credentials from config
    credentials = Config ()
    users = credentials.get ('users')
    download_folder = credentials.get ('download_folder')

    # Instance of twitter scraper
    twitter_scraper = TwitterScraper (users, download_folder)
    twitter_scraper.extract ()


if __name__ == "__main__":
    main ()