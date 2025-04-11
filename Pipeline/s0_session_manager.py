import os
import time
import pickle
import logging
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from Pipeline.util_human_mimic import human_sleep, human_scroll, random_hover
from Pipeline.util_paths import (
    resource_path,
    get_persistent_data_path,
    ensure_dir,
    load_config
)


# This class handles the login session with LinkedIn, including loading and saving cookies,


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class SessionManager:
    def __init__(self, cookie_path="your_cookies.pkl", use_user_profile=True, user_profile_path=None):
        self.use_user_profile = use_user_profile
        config = load_config()

        #determine Chrome profile path
        if self.use_user_profile:
            if user_profile_path:
                self.user_profile_path = user_profile_path
            elif "chrome_profile_path" in config:
                self.user_profile_path = config["chrome_profile_path"]
            else:
                #default: persistent profile dir inside LOCALAPPDATA
                self.user_profile_path = ensure_dir("chrome_profile")
            logging.info(f"[CHROME] Using Chrome profile at: {self.user_profile_path}")
        else:
            self.user_profile_path = None
            logging.warning("[CHROME] Using temporary profile (less stealthy)")

        #persistent cookie file
        self.cookie_path = get_persistent_data_path(cookie_path)

        #this loads up the browser
        self.driver = self._init_driver()
        
        #initialise the driver, setting various options and arguements
    def _init_driver(self):
        chromedriver_autoinstaller.install()
        options = Options()
        options.add_argument("--user-agent=Mozilla/5.0")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        if self.use_user_profile and self.user_profile_path:
            options.add_argument(f"--user-data-dir={self.user_profile_path}")
            options.add_argument("--profile-directory=Default")
            logging.info(f"Using Chrome profile at {self.user_profile_path}")
        else:
            logging.warning("Launching with temporary Chrome profile")

        driver = webdriver.Chrome(options=options)
        driver.set_window_position(0, 0)
        driver.set_window_size(1200, 1000)

        logging.debug(f"Chrome launched with profile: {self.user_profile_path}")
        logging.debug(f"Cookies will be saved to: {self.cookie_path}")
        return driver

    def _human_mimic(self):
        human_scroll(self.driver, total_scrolls=5)
        random_hover(self.driver)
        human_sleep(2, 0.5)
 
    #saves cookies so you dont have to manual login repeatedly
    def _save_cookies(self):
        try:
            with open(self.cookie_path, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            logging.info(f"Cookies saved to {self.cookie_path}")
        except Exception as e:
            logging.error(f"Failed to save cookies: {e}")

    #loads cookies from the file
    def _load_cookies(self):
        if not os.path.exists(self.cookie_path):
            logging.warning(f"Cookie file not found at {self.cookie_path}")
            return

        try:
            with open(self.cookie_path, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    if 'domain' in cookie and "linkedin" not in cookie["domain"]:
                        continue
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logging.debug(f"Failed to load a cookie: {e}")
        except Exception as e:
            logging.error(f"Failed to load cookies: {e}")

    #login function, either you manual login or if they are still valid, default to cookies
    def _wait_for_login(self, timeout=120):
        logging.info("Waiting for successful login...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if "feed" in self.driver.current_url:
                logging.info("Login detected.")
                return True
            time.sleep(2)
        return False

    def login(self):
        self.driver.get("https://www.linkedin.com")
        time.sleep(3)

        if os.path.exists(self.cookie_path):
            self._load_cookies()
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            self.driver.refresh()
            time.sleep(2)

            if "feed" in self.driver.current_url:
                logging.info("Logged in using saved cookies.")
                self._human_mimic()
                return self.driver
            else:
                logging.warning("Saved cookies invalid or expired.")

        logging.info("Manual login required. Opening login page...")
        self.driver.get("https://www.linkedin.com/login")

        if self._wait_for_login():
            self._save_cookies()
            self._human_mimic()
        else:
            logging.error("Login not detected within timeout.")

        return self.driver

    def get_driver(self):
        return self.driver
    #function for closing the driver gracefully
    def close(self):
        if self.driver:
            self.driver.quit()
            logging.info("Driver closed.")
