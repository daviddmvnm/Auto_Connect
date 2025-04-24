import os
import random
import time
import sqlite3
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from Pipeline.util_human_mimic import human_sleep, human_scroll, random_hover, take_linkedin_detour
from Pipeline.util_paths import get_persistent_data_path, load_config, ensure_dir

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


#so now we've saved a mass of profiles urls and names and ids, we want to get all the raw html for processing,
#i decided to take all the html because well, in the future i might add or create new features so, it'll be nice to have if i need to scrape new stuff from profiles

class HTMLExtraction:
    def __init__(self, driver, db_filename="linkedin_profiles.db", cache_subdir="html_cache"):
        self.driver = driver
        self.db_path = self._get_db_path(db_filename)
        self.cache_dir = self._get_cache_dir(cache_subdir)

        self.pause_after_n = random.randint(5, 10)
        self.processed_count = 0

        logging.debug(f"DB path: {self.db_path}")
        logging.debug(f"Cache folder: {self.cache_dir}")

    def _get_db_path(self, filename):
        path = get_persistent_data_path(filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
    
    #in our data/ folder we     have a folder called html_cache, this is where we save all the html files
    #this is a subfolder of the persistent data path, so we can find it easily
    def _get_cache_dir(self, subfolder):
        base_dir = os.path.dirname(self.db_path)
        cache_path = os.path.join(base_dir, subfolder)
        os.makedirs(cache_path, exist_ok=True)
        return cache_path

    #sort by profile id nad then we go page to page
    def load_profiles(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT profile_id, profile_url FROM profiles ORDER BY profile_id ASC").fetchall()
        except Exception as e:
            logging.error(f"Failed to load profiles: {e}")
            return []

    #scraping rawhtml from the profile page
    def save_profile_html(self, profile_id, url):
        filename = f"profile_{profile_id}.html"
        filepath = os.path.join(self.cache_dir, filename)
        
        #if the profile_id has already been saved, we skip it
        #this is a good way to avoid re-downloading the same profile over and over again
        if os.path.exists(filepath):
            logging.info(f"[{profile_id}] Skipped — already saved.")
            return False

        logging.info(f"[{profile_id}] Visiting: {url}")
        try:
            self.driver.get(url)

            human_sleep(3, 15)
            human_scroll(self.driver, total_scrolls=random.randint(2, 5))
            if random.random() < 0.3:
                time.sleep(random.uniform(1, 10))
                human_scroll(self.driver, total_scrolls=random.randint(1, 5))

            random_hover(self.driver, "section")
            
            if random.random() < 0.2:
                take_linkedin_detour(self.driver)
                human_sleep(random.uniform(10, 20))

            if random.random() < 0.4:
                random_hover(self.driver, random.choice(["h1", "h2", "section", "img"]))
                human_sleep(random.uniform(0.5, 2))

            html = self.driver.page_source

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            logging.info(f"[{profile_id}] Saved HTML.")
            return True

        except Exception as e:
            logging.error(f"[{profile_id}] Error: {e}")
            return False

        finally:
            self.processed_count += 1

            if random.random() < 0.1:
                take_linkedin_detour(self.driver)

            if self.processed_count >= self.pause_after_n:
                long_break = random.uniform(10, 20)
                logging.info(f"\n--- Long break: {long_break:.1f} seconds ---\n")
                time.sleep(long_break)
                self.processed_count = 0
                self.pause_after_n = random.randint(10, 30)

    def run(self, max_profiles=None):
        profiles = self.load_profiles()
        logging.info(f"\nLoaded {len(profiles)} profiles from database.\n")

        saved = 0
        for profile_id, url in profiles:
            was_saved = self.save_profile_html(profile_id, url)
            if was_saved:
                saved += 1
                if max_profiles is not None and saved >= max_profiles:
                    logging.info(f"\n[INFO] Reached max of {max_profiles} new profiles. Stopping.\n")
                    break

        logging.info(f"\n[SUCCESS] HTML extraction complete. {saved} new profiles saved.")
        logging.info(f"[INFO] Processed {self.processed_count} profiles in total.")
        logging.info(f"[INFO] All HTML files saved in: {self.cache_dir}")
        logging.info(f"[INFO] DB path: {self.db_path}")
        logging.info(f"[INFO] Cache folder: {self.cache_dir}\n")
