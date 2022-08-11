import os
import time
from tqdm import tqdm
from logs import logger
from scraping_manager.automate import Web_scraping
from spreadsheet_manager.xlsx import SS_manager
from selenium.webdriver.common.by import By

class TwitterScraper ():

    def __init__ (self, users:list=[], download_folder=""):
        """Start scraper and setup options

        Args:
            users (list, optional): List fo users to get followers data. Defaults to [].
            max_followers (int, optional): Maz followers to get from each user. Defaults to None.
            max_minutes (int, optional): maz minutes to run the scraper for each user. Defaults to None.
        """
        
        logger.info ("Running scraper...")
        
        # Scraper options
        self.__users = users

        # Chrome folder
        user_name = os.getlogin()
        chrome_folder = f"C:\\Users\\{user_name}\\AppData\\Local\\Google\\Chrome\\User Data"

        # Start browser
        self.__download_folder = download_folder
        self.__home_page = "https://www.vicinitas.io/"
        self.__scraper = Web_scraping (chrome_folder=chrome_folder, 
                                        start_killing=True, 
                                        download_folder=self.__download_folder, 
                                        web_page=self.__home_page)

        # Global followers_data
        self.__followers_data = []

    def extract (self):

        for user in self.__users:
            
            # Search and download file
            self.__download_files (user)

            # Validate if page requiered twitter autorization
            requiere_autorization = self.__requiere_autorization ()
            if requiere_autorization:
                self.__autorize()

            # Wait for download file
            selector_progress = "#info > b"
            while True:

                wait = True
                self.__scraper.refresh_selenium ()

                # Get current progress
                progress = self.__scraper.get_text (selector_progress)
                if progress:
                    progress_parts = list(map (lambda elem: elem.strip(), progress.split ("/")))

                    # Validate if the page finish
                    if progress_parts[0] == progress_parts[1]:
                        wait = False
                
                if wait:
                    time.sleep (20)
                    continue
                else:
                    break 

            # Download file
            selector_download = "#info .btn.btn-success"
            self.__scraper.click (selector_download)
            time.sleep (5)

            # Return to main page
            self.__scraper.set_page (self.__home_page)

    def __download_files (self, user):
        # Search  user and download file
        selector_followers = "#r3"
        selector_search = "#tracker"
        selector_submit = "#free_btn"
        self.__scraper.click_js (selector_followers)
        self.__scraper.send_data (selector_search, user)
        self.__scraper.click_js (selector_submit)

    def __requiere_autorization (self):
        
        """Check if the page need twitter autorization for continue

        Returns:
            bool: return True if the the page requieres autorization
        """

        time.sleep (2)
        self.__scraper.refresh_selenium ()
        selector_login = "#btn_login"
        text_login = self.__scraper.get_text (selector_login)
        if text_login:
            return True
        else:
            return False

    def __autorize (self):
        """ Autorize and detect if it requiered manual login o autorization
        """

        # Login with twitter, if its required
        selector_login = "#btn_login"
        self.__scraper.click (selector_login)

        # Validate if manual login its required
        current_url = self.__scraper.driver.current_url
        if "api.twitter.com" in current_url:
            logger.warning ("Manual login or autorization is required.\nPlease login or autorize and press enter to continue.")

    def __add_column (self):
        print ("done")
        



