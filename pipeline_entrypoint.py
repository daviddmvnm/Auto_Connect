from Pipeline.util_paths import load_config, get_persistent_data_path
from Pipeline.s0_session_manager import SessionManager
from Pipeline.s1_shallow_scraper import ShallowScraper
from Pipeline.s2_html_extraction import HTMLExtraction
from Pipeline.s3_profile_parser import ProfileParser
from Pipeline.s4_preprocessing import DataPreprocessing
from Pipeline.s5_ml_layer import ModelPredictor
from Pipeline.s6_outreach_eval import (
    linkedin_outreach_from_df,
    get_all_connections,
    update_connection_accepted,
    load_acceptance_metrics,
)

import os
import logging
import pandas as pd


def collect_and_prepare_data():
    """
    Runs the full data collection and ML prediction pipeline:
    1. Scrapes shallow profile data from LinkedIn.
    2. Extracts and saves full HTML for each profile.
    3. Parses cached HTML to structured profile data.
    4. Applies cleaning and tagging logic.
    5. Feeds processed data into an ML model and populates outreach queue.
    
    Compatible with both standard and frozen (.exe) environments.
    """
    config = load_config()
    target_label = config.get("target_label", "University of Exeter")
    max_profiles = config.get("max_profiles", 5)

    session = SessionManager()
    driver = session.login()

    try:
        # 1. Scrape LinkedIn profiles
        scraper = ShallowScraper(driver)
        if scraper.wait_and_open_target_tab(target_label):
            df = scraper.scroll_and_extract_profiles(max_profiles=max_profiles)
            scraper.save_to_database(df)
        else:
            logging.error("[ERROR] Could not open target tab.")
            return

        # 2. Extract full HTML
        extractor = HTMLExtraction(driver)
        extractor.run(max_profiles=max_profiles)

        # 3. Parse profiles from HTML
        parser = ProfileParser()
        html_cache = os.path.join(os.path.dirname(get_persistent_data_path("linkedin_profiles.db")), "html_cache")
        profile_ids = [
            int(f.split("_")[1].split(".")[0])
            for f in os.listdir(html_cache)
            if f.startswith("profile_") and f.endswith(".html")
        ]

        parsed_profiles = []
        for pid in sorted(profile_ids):
            parsed = parser.parse_profile(pid)
            if parsed:
                parsed_profiles.append(parsed)
                logging.info(f"[PARSED] ID {pid}: {len(parsed['experiences'])} roles, {parsed['connection_count']} connections.")

        # 4. Preprocess and tag
        if parsed_profiles:
            df_raw = pd.DataFrame(parsed_profiles)
            processor = DataPreprocessing(df_raw)
            processor.run_cleaning()
            processor.run_tagging()
            processor.save_to_database()
        else:
            logging.warning("[SKIP] No parsed profiles to process.")

        # 5. Run prediction and update outreach queue
        model = ModelPredictor()
        df_predicted = model.run()
        logging.info(f"[ML] {len(df_predicted)} profiles added to database.")

    finally:
        session.close()


def send_connection_invites(driver=None):
    """
    Sends connection invites using provided driver.
    If no driver is provided, a new session is started.
    """
    config = load_config()
    max_invites = config.get("max_invites", 5)

    session = None
    if driver is None:
        session = SessionManager()
        driver = session.login()

    try:
        linkedin_outreach_from_df(driver=driver, max_invites=max_invites, keep_driver_open=True)
    finally:
        if session:
            session.close()


def refresh_connection_tracking(driver=None):
    """
    Refreshes the local database based on current accepted LinkedIn connections.
    """
    session = None
    if driver is None:
        session = SessionManager()
        driver = session.login()

    try:
        accepted_names = get_all_connections(driver)
        update_connection_accepted(accepted_names)

        sent, accepted, rate = load_acceptance_metrics()
        logging.info(f"[STATS] Sent: {sent} | Accepted: {accepted} | Rate: {rate:.2f}%")
    finally:
        if session:
            session.close()

