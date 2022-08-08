import os
import time
import csv
from logs import logger
from scraping_manager.automate import Web_scraping
from spreadsheet_manager.xlsx import SS_manager

class TwitterScraper ():

    def __init__ (self, save_columns:dict, max_tweets:int = None, max_time:int = None):
        """Start scraper and setup options

        Args:
            max_tweets (int): number of max tweets to scrape (optional)
            max_time (int): number of max minutes to run the scraper (optional)
        """
        
        logger.info ("Running scraper...")

        # Class scraping data variables
        self.__tweets_ids = []
        self.__tweets_counter = 0
        self.__start_time = time.time ()
        self.__tweets_data = []
        
        # Scraper options
        self.__max_tweets = max_tweets
        self.__max_time = max_time
        self.__save_columns = list (filter (lambda column: save_columns[column], save_columns.keys()))

        # Save header in data
        header = list(map (lambda elem: elem.title(), self.__save_columns))
        self.__tweets_data.append (header)

        # Chrome folder
        user_name = os.getlogin()
        chrome_folder = f"C:\\Users\\{user_name}\\AppData\\Local\\Google\\Chrome\\User Data"

        # Start browser
        self.__home_page = "https://twitter.com/"
        self.__scraper = Web_scraping (chrome_folder=chrome_folder, start_killing=True)

        # Connect to excel and clean last sheets
        output_path = os.path.join (os.path.dirname(__file__), "data.xlsx")
        self.__ss_manager = SS_manager (output_path)
        self.__ss_manager.clean_workbook ()

        # Class css selectors
        self.__selector_tweet_wrapper = '[aria-labelledby].css-1dbjc4n > .css-1dbjc4n > div > div'

    def set_filters (self, start_date:str, end_date:str, keywords:list=[], hashtags:list=[], users:list=[]):
        """ Search tweets using filters

        Args:
            keywords (list): keywords to search in the tweets
            hashtags (list): hashtags to search in the tweets
            users (list): user who tweeted
            start_date (str): startd ate in format YYYY-MM-DD
            end_date (str): end ate in format YYYY-MM-DD
        """

        if keywords:
            logger.info (f"\nKeywords: {', '.join (keywords)}")

        # Serach variables
        self.__keywords = keywords
        self.__hashtags = hashtags
        self.__users = users
        self.__start_date = start_date
        self.__end_date = end_date

    def __search (self, start_date:str, end_date:str):
        """Go to twitter home page and search the filter options with specific dates

        Args:
            start_date (str): start date for search tweets. Format: YYYY-MM-DD
            end_date (str): end date for search tweets. Format: YYYY-MM-DD
        """

        # Sarch variables
        search_query = ""
        search_parts = []

        # Format search variables
        if self.__keywords:
            keywords_formated = " OR ".join(self.__keywords)
            search_parts.append (f"({keywords_formated})")
        
        if self.__hashtags:
            hashtags_formated = " OR ".join(self.__hashtags)
            search_parts.append (f"({hashtags_formated})")
        
        if self.__users:
            users_list = []
            for user in self.__users:
                users_list.append (f"from:{user}")
            users_formated = " OR ".join (users_list)
            search_parts.append (f"({users_formated})")

        if self.__start_date:
            search_parts.append (f"since:{start_date}")

        if self.__end_date:
            search_parts.append (f"until:{end_date}")

        # Format query
        search_query = " ".join (search_parts)

        # Sarch tweets 
        self.__scraper.set_page (self.__home_page)
        selector_search = 'input[data-testid="SearchBox_Search_Input"]'
        self.__scraper.wait_load (selector_search, time_out=60)
        self.__scraper.send_data (selector_search, search_query)
        self.__scraper.send_data (selector_search, "\n")
        time.sleep (5)
        self.__scraper.refresh_selenium ()

    def __generate_search_dates (self):
        """Create a lñost of searct dates with the nested list: [start_date, end_date], 
        for scrape the data by month
        """

        self.__search_dates = []
        start_year, start_month, start_day = list(map (lambda x: int(x), self.__start_date.split("-")))
        end_year, end_month, end_day = list(map (lambda x: int(x), self.__end_date.split("-")))
        search_start_year, search_start_month, search_start_day = start_year, start_month, start_day

        # Data in the same month
        if start_year == end_year and start_month == end_month:
            self.__search_dates.append ([
                self.__start_date,
                self.__end_date,
            ])
        
        # Multiple months
        else:
            while True:

                search_end_year, search_end_day = search_start_year, search_start_day

                # Calculate next month
                search_end_month = search_start_month + 1
                if search_end_month == 13:
                    search_end_month = 1
                    search_end_year += 1

                # Format months and dates
                search_start_month_formated = f"0{search_start_month}" if len (str(search_start_month)) == 1 else search_start_month
                search_end_month_formated = f"0{search_end_month}" if len (str(search_end_month)) == 1 else search_end_month
                search_start_day_formated = f"0{search_start_day}" if len (str(search_start_day)) == 1 else search_start_day
                search_end_day_formated = f"0{search_end_day}" if len (str(search_end_day)) == 1 else search_end_day
    
                # Save search dates
                self.__search_dates.append ([
                    f"{search_start_year}-{search_start_month_formated}-{search_start_day_formated}",
                    f"{search_end_year}-{search_end_month_formated}-{search_end_day_formated}",
                ])
                
                # Update start values
                search_start_year, search_start_month, search_start_day = search_end_year, search_end_month, search_end_day

                # last month to scrape and end loop
                if search_start_year >= end_year and search_end_month >= end_month:
                    self.__search_dates.append ([
                        f"{search_end_year}-{search_end_month_formated}-{search_start_day_formated}",
                        f"{search_end_year}-{search_end_month_formated}-{end_day}",
                    ])

                    break

    def __extract (self):
        """ Extract tweets in current page
        """

        # Restart running status
        running = True

        # Scrape tweets
        while running:
    
            # Get total of tweets
            tweets_num = len(self.__scraper.get_elems (self.__selector_tweet_wrapper))
            
            # Control variable for detect if the page have not more tweets
            more_tweets = False

            for tweet_num in range (1, tweets_num + 1):

                # Selectors
                selector_tweet = f"{self.__selector_tweet_wrapper}:nth-child({tweet_num}) .css-1dbjc4n > article"
                selector_tweet_user = f'{selector_tweet} div[dir="ltr"] .css-901oao'
                selector_tweet_date = f'{selector_tweet} time[datetime]'
                selector_tweet_text = f'{selector_tweet} .css-1dbjc4n > div[lang]'
                selector_tweet_links = f'{selector_tweet} a'
                selector_tweet_img = f'{selector_tweet} [data-testid="tweetPhoto"] > img[draggable="true"]'
                selector_tweet_counters = f'{selector_tweet} .css-1dbjc4n .css-1dbjc4n .css-1dbjc4n.r-1ta3fxp.r-18u37iz.r-1wtj0ep.r-1s2bzr4 > .css-1dbjc4n.r-18u37iz.r-1h0z5md'
                selector_tweet_comments = f'{selector_tweet_counters}:nth-child(1)'
                selector_tweet_retweets = f'{selector_tweet_counters}:nth-child(2)'
                selector_tweet_likes = f'{selector_tweet_counters}:nth-child(3)'

                # Extract id items
                tweet_data = []
                tweet_user = self.__scraper.get_text (selector_tweet_user)
                tweet_date = self.__scraper.get_attrib (selector_tweet_date, "datetime")

                # Extract, process data and save
                if "user" in self.__save_columns:
                    tweet_data.append (tweet_user)

                if "date" in self.__save_columns:
                    tweet_data.append (tweet_date)

                # Generate tweet id and validate
                tweet_id = f"{tweet_user}{tweet_date}"
                if tweet_id in self.__tweets_ids:
                    continue
                more_tweets = True
    
                if "text" in self.__save_columns:
                    tweet_text = self.__scraper.get_text (selector_tweet_text)
                    
                    # Clean text
                    if tweet_text:
                        tweet_text = str(tweet_text).strip ().replace("'", "").replace('"', "").replace ("\n", " ")
                    else:
                        continue

                    tweet_data.append (tweet_text)

                if "links" in self.__save_columns:
                    tweet_links = self.__scraper.get_attribs (selector_tweet_links, "href")

                    # Clean links
                    temp_links = tweet_links[:]
                    tweet_links = []
                    for link in temp_links:
                        if "twitter" not in link:
                            tweet_links.append (link)

                    tweet_data.append (" ".join (tweet_links))

                if "hashtags" in self.__save_columns:
                    tweet_hashtags = []
                    for word in tweet_text.split(" "):
                        if word not in tweet_hashtags:
                            word_clean = word.strip()

                            if "#" in word_clean:
                                tweet_hashtags.append (word_clean)
                    
                    tweet_data.append (" ".join (tweet_hashtags))

                if "mentions" in self.__save_columns:
                    tweet_mentions = []
                    for word in tweet_text.split(" "):
                        if word not in tweet_mentions:
                            word_clean = word.strip()

                            if "@" in word_clean:
                                tweet_mentions.append (word_clean)

                    tweet_data.append (" ".join (tweet_mentions))

                if "img" in self.__save_columns:
                    tweet_img = self.__scraper.get_attrib (selector_tweet_img, "src")

                    if not tweet_img:
                        tweet_img = ""

                    tweet_data.append (tweet_img)
                
                if "comments" in self.__save_columns:
                    tweet_comments = self.__scraper.get_text (selector_tweet_comments)

                    # Clean counter
                    tweet_comments = tweet_comments if tweet_comments else "0"

                    tweet_data.append (tweet_comments)

                if "retweets" in self.__save_columns:
                    tweet_retweets = self.__scraper.get_text (selector_tweet_retweets)

                    # Clean counter
                    tweet_retweets = tweet_retweets if tweet_retweets else "0"

                    tweet_data.append (tweet_retweets)

                if "likes" in self.__save_columns:
                    tweet_likes = self.__scraper.get_text (selector_tweet_likes)

                    # Clean counter
                    tweet_likes = tweet_likes if tweet_likes else "0" 

                    tweet_data.append (tweet_likes)

                # Save current tweet data
                self.__tweets_data.append (tweet_data)
                self.__tweets_ids.append (tweet_id)

                # Validate max tweets
                self.__tweets_counter+=1
                if self.__max_tweets:
                    if self.__tweets_counter > self.__max_tweets:
                        running = False
                
                # Validate max time
                end_time = time.time ()
                total_time = (end_time - self.__start_time)/60
                if self.__max_time:
                    if total_time >= self.__max_time:
                        running = False
            
            # Validete if the page have not more tweets
            if not more_tweets:
                running = False

            # Loads next tweets
            for _ in range (4):
                self.__scraper.go_down ("body")
                time.sleep (1)
            time.sleep (5)
            self.__scraper.refresh_selenium ()


    def set_sheet (self, output_sheet:str):
        """Create and set new sheet in excel file for save data"""

        # Connect to google sheets
        self.__ss_manager.create_get_sheet (output_sheet)

    def __save_excel (self):
        """Save data in current excel sheet"""

        # Write data in excel
        self.__ss_manager.write_data (self.__tweets_data)
        self.__ss_manager.auto_width ()
        self.__ss_manager.save ()

    def extract_by_dates (self):
        """Extract data and save in excel

        Args:
            output_sheet (str): name of the file to save the data, like "output" (without extension)
        """

        logger.info (f"\tScraping data...")

        # Search dates for each month
        self.__generate_search_dates ()

        for start_date, end_date in self.__search_dates:

            # Update filters
            self.__search (start_date, end_date)

            # Debug
            logger.info (f"\tScraping data from {start_date} to {end_date}...")

            # Scrape tweets in current page
            self.__extract ()

        self.__save_excel ()

        # End message
        logger.info (f"\tDone")

    def extract_liked_tweets (self):
        """Go to liked tweets section in user profile, for download all tweets"""

        logger.info ("Loading liked tweets...")

        self.__scraper.set_page (self.__home_page)
        time.sleep (3)
        self.__scraper.refresh_selenium ()

        # Open profile page
        selector_profile_btn = 'nav[aria-label="Primary"] > a:nth-child(7)'
        link = self.__scraper.get_attrib (selector_profile_btn, "href")
        self.__scraper.set_page (link)
        time.sleep (3)
        self.__scraper.refresh_selenium ()

        # Go to liked tweets tab
        selector_liked_btn = 'div[role="tablist"] > div:last-child > a'
        link = self.__scraper.get_attrib (selector_liked_btn, "href")
        self.__scraper.set_page (link)
        time.sleep (3)
        self.__scraper.refresh_selenium ()

        logger.info ("Scraping liked tweets...")
        self.__extract ()
        self.__save_excel ()
        logger.info ("Done")