import os
import sys
import random
import sqlite3
import logging
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from functions.human_mimic import human_sleep, random_hover
from functions.utils import get_persistent_data_path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

#this class handles basic scraping, from the people you may know page
#nothing extensive jsut basics like header, name, and url

class ShallowScraper:
    def __init__(self, driver):
        self.driver = driver
        self.people = []
        self.db_filename = "linkedin_profiles.db"
        self.db_path = self._get_db_path()
        self.seen_urls = self._load_seen_urls()
        self.original_window_size = self.driver.get_window_size()

   ##this function is used to get the path to the database file, neccessary for bundling 
    def _get_db_path(self):
        path = get_persistent_data_path(self.db_filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    #loads urls we've already seen to prevent repeat scrapes
    def _load_seen_urls(self):
        seen = set()
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT profile_url FROM profiles")
                seen.update(row[0] for row in cursor.fetchall())
                conn.close()
                logging.info(f"Loaded {len(seen)} previously scraped URLs from DB.")
            except Exception as e:
                logging.error(f"Could not load seen URLs: {e}")
        return seen

    #this makes the window fullscreen, I had to do this to trigger lazy load
    #it's annoying but required for functionality, passable to me for a prototype
    ### TO SELF: this is a temporary fix, I need to find a better way to do this

    def temporarily_resize_window(self):
        try:
            self.driver.set_window_position(0, 0)
            self.driver.fullscreen_window()
            human_sleep(1, 0.5)
        except Exception as e:
            logging.warning(f"Could not resize window: {e}")

    #exiting fullscreen
    def reset_window_size(self):
        self.driver.set_window_size(
            self.original_window_size['width'],
            self.original_window_size['height']
        )
        human_sleep(1, 0.5)
    
    #gradually scroll around a profile
    def gradual_scroll(self, pixels=300, steps=10, delay_range=(0.2, 0.4)):
        for _ in range(steps):
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            human_sleep(*delay_range)
    #opens the desired section, max retries here is excesive but you now just to be sure i guess
    def wait_and_open_target_tab(self, target_label, max_retries=10, scroll_loops=3):
        logging.info(f"Trying to open 'People you may know from {target_label}' tab")
        
        #the loop that actually looks for the target tab
        for attempt in range(max_retries):
            logging.info(f"[{attempt + 1}/{max_retries}] Searching...")
            self.driver.get("https://www.linkedin.com/mynetwork/")
            human_sleep(5, 2)
            random_hover(self.driver, "a")
            self.temporarily_resize_window()

            self.driver.execute_script("window.scrollBy(0, 500);")
            human_sleep(1.5, 0.5)
            self.driver.execute_script("""
                const evt = new WheelEvent('wheel', {
                    deltaY: 100,
                    bubbles: true,
                    cancelable: true
                });
                document.dispatchEvent(evt);
            """)
            human_sleep(1.5, 0.5)
            #scroll to look for the tabs and force lazy load
            for scroll in range(scroll_loops):
                logging.info(f"    Gradual scroll {scroll + 1}/{scroll_loops}")
                self.gradual_scroll()
                if scroll in {2, 5} and random.random() < 0.4:
                    logging.info("   ...pausing to simulate reading")
                    human_sleep(3, 1)
            
            #then try to click it, if it's not there... reload and rescroll
            try:
                show_all_btn = self.driver.find_element(
                    By.XPATH,
                    f"//button[contains(@aria-label, 'People you may know') and contains(@aria-label, '{target_label}')]"
                )
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth' });", show_all_btn)
                human_sleep(2, 1)
                ActionChains(self.driver).move_to_element(show_all_btn).perform()
                human_sleep(1.5, 0.5)
                self.driver.execute_script("arguments[0].click();", show_all_btn)
                logging.info(f"Opened suggestions for: {target_label}")
                self.reset_window_size()
                return True
            except Exception:
                logging.warning("Did not find the tab this time.")
                if random.random() < 0.5:
                    self.driver.get("https://www.linkedin.com/feed/")
                    logging.info("Went back to feed to reset.")
                else:
                    logging.info("Retrying directly from My Network...")
                human_sleep(5, 2)

        logging.error("Gave up after too many attempts. Are you sure you entered the section name EXACTLY?")
        return False
    


    #this function is used to grab profile data
    def scroll_and_extract_profiles(self, pause_range=(2.5, 4.0), streak_limit=5, scrolls_per_loop=5,
                                     scroll_factor=1.8, max_profiles=100):
        streak = 0
        loop = 0
        #try to get the cointer
        def get_scroll_container(timeout=10):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#root > dialog > div > div:nth-child(2)"))
                )
            except Exception:
                return None
        #once we grab the container we basically just loop down and click load more until either we hit the desired n or names stop loading
        def extract_new_people():
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("a", href=True)
            new_count = 0

            for card in cards:
                href = card['href']
                if not href.startswith("https://www.linkedin.com/in/") or href in self.seen_urls:
                    continue
                try:
                    paragraphs = card.find_all("p")
                    if len(paragraphs) < 2:
                        continue
                    name = paragraphs[0].get_text(strip=True)
                    headline = paragraphs[1].get_text(strip=True)
                    self.people.append({
                        "name": name,
                        "headline": headline,
                        "profile_url": href
                    })
                    self.seen_urls.add(href)
                    new_count += 1
                    if max_profiles and len(self.people) >= max_profiles:
                        break
                except Exception as e:
                    logging.debug(f"Error parsing card: {e}")
                    continue
            return new_count

        logging.info("\nStarting deep scroll & extract...\n")

        while True:
            loop += 1
            logging.info(f"Loop {loop}")
            new_profiles = extract_new_people()
            logging.info(f"   New: {new_profiles} | Total collected: {len(self.people)}")

            if max_profiles and len(self.people) >= max_profiles:
                logging.info(f"Reached max scrape limit ({max_profiles}). Stopping.")
                break

            if new_profiles == 0:
                streak += 1
                logging.info(f"   No new profiles ({streak}/{streak_limit})")
                if streak >= streak_limit:
                    logging.info("Too many empty scrolls. Ending loop.")
                    break
            else:
                streak = 0

            scroll_container = get_scroll_container()
            if scroll_container and scroll_container.size['height'] > 0:
                logging.info("Using modal container for scrolling.")
                try:
                    for s in range(scrolls_per_loop):
                        factor = scroll_factor + random.uniform(-0.3, 0.3)
                        self.driver.execute_script("""
                            let container = arguments[0];
                            container.scrollTop += container.clientHeight * arguments[1];
                        """, scroll_container, factor)
                        logging.info(f"      Modal scroll {s+1}/{scrolls_per_loop} [factor: {factor:.2f}]")
                        human_sleep(random.uniform(1.5, 2.5))
                except Exception as e:
                    logging.warning(f"   Failed modal scroll: {e}")
                    self.gradual_scroll()
            else:
                logging.info("Modal container missing. Using full-page scroll.")
                for s in range(scrolls_per_loop):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    logging.info(f"      Full-page scroll {s+1}/{scrolls_per_loop}")
                    human_sleep(random.uniform(1.5, 2.5))

            try:
                see_more_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "#root > dialog > div > div > div > div > section > div > div > div > div._1xoe5hdi.cnuthtrs > button"
                )
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth' });", see_more_button)
                human_sleep(2, 1)
                ActionChains(self.driver).move_to_element(see_more_button).perform()
                human_sleep(1.5, 0.5)
                self.driver.execute_script("arguments[0].click();", see_more_button)
                human_sleep(2, 1)
            except Exception:
                logging.debug("   No 'See more' button found this round.")

            if loop % 3 == 0 and random.random() < 0.5:
                pause = random.uniform(5, 9)
                logging.info(f"   Taking a longer pause: {pause:.1f}s")
                human_sleep(pause / 2, pause / 2)

            human_sleep(*pause_range)

        df = pd.DataFrame(self.people)
        logging.info(f"\nDone. Collected {len(df)} unique profiles.\n")
        return df
    
    #takes our df of scraped names and drops them to a permanent sqlite3 database
    def save_to_database(self, df):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)  #saftey

        logging.debug(f"Saving DB to: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_url TEXT UNIQUE,
                name TEXT,
                headline TEXT,
                location TEXT,
                connections TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        new_rows = 0
        if not df.empty:
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO profiles (profile_url, name, headline, location, connections)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get("profile_url"),
                        row.get("name"),
                        row.get("headline"),
                        row.get("location", None),
                        row.get("connections", None)
                    ))
                    new_rows += 1
                except sqlite3.IntegrityError:
                    continue
            conn.commit()
            logging.info(f"Inserted {new_rows} new profiles into the database.")
        else:
            logging.info("No profiles scraped to insert.")

        conn.close()
