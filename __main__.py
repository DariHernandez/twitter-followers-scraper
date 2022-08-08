from config import Config
from twitter_scraper import TwitterScraper

def main ():
    # Get credentials from config
    credentials = Config ()
    keywords = credentials.get ("keywords")
    hashtags = credentials.get ("hashtags")
    users = credentials.get ("users")
    start_date = credentials.get ("start_date")
    end_date = credentials.get ("end_date")
    max_tweets = credentials.get ("max_tweets")
    max_time = credentials.get ("max_time")
    separated_keywords = credentials.get ("separated_keywords")
    save_columns = credentials.get ("save_columns")
    search_filters = credentials.get ("search_filters")
    only_liked_tweets = credentials.get ("only_liked_tweets")

    # Instance of twitter scraper
    twitter_scraper = TwitterScraper (save_columns, max_tweets, max_time)

    if search_filters:
        if separated_keywords:
            for keywords_sublist in keywords:

                # Convert serach to list
                if type(keywords_sublist) == str:
                    keywords_sublist = [keywords_sublist]

                # Set filter for each
                twitter_scraper.set_filters (start_date, end_date, keywords_sublist, hashtags, users)
                output_sheet = " ".join (keywords_sublist)
                twitter_scraper.set_sheet (output_sheet)
                twitter_scraper.extract ()
        else:
            # Set filters for current keyword
            twitter_scraper.set_filters (start_date, end_date, keywords, hashtags, users)
            twitter_scraper.set_sheet ("found tweets")
            twitter_scraper.extract_by_dates ()    

    if only_liked_tweets:
        twitter_scraper.set_filters (start_date, end_date)
        twitter_scraper.set_sheet ("liked tweets")
        twitter_scraper.extract_liked_tweets ()


if __name__ == "__main__":
    main ()