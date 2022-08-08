from config import Config
from twitter_scraper import TwitterScraper

def main ():
    # Get credentials from config
    credentials = Config ()
    users = credentials.get ('users')
    max_followers = credentials.get ('max_followers')

    # Instance of twitter scraper
    twitter_scraper = TwitterScraper (users, max_followers)
    twitter_scraper.extract ()


if __name__ == "__main__":
    main ()