import os
import sys
import sqlite3
import random
import time
import pandas as pd
import logging
import traceback
from datetime import datetime, timezone, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from Pipeline.util_human_mimic import human_scroll, human_sleep, random_hover, take_linkedin_detour, force_stabilize_view
from Pipeline.util_paths import get_persistent_data_path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

CONNECT_BUTTON_XPATH = "//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'connect')]"
SEND_WITHOUT_MESSAGE_SELECTOR = "button[aria-label='Send without a note']"

def safe_click(driver, element, url=None, label="", retries=2):
    for attempt in range(retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            element.click()
            return
        except WebDriverException as e:
            logging.warning(f"[WARN] Click attempt {attempt+1} failed for {label} at {url}: {e}")
            time.sleep(1)
        try:
            driver.execute_script("arguments[0].click();", element)
            logging.warning(f"[FALLBACK] JS click used for {label} at {url}")
            return
        except Exception as e2:
            error_msg = ''.join(traceback.format_exception_only(type(e2), e2)).strip()
            logging.error(f"[ERROR] Could not click {label} at {url}: {error_msg}")
            if attempt == retries - 1:
                raise

def linkedin_outreach_from_df(
        #add a timestamping feature
    driver=None,
    load_driver_func=None,
    max_invites=30,
    batch_size_range=(5, 10),
    break_duration_range=(45, 90),
    db_filename="linkedin_profiles.db",
    keep_driver_open=True,
    min_acceptance_threshold=0.01
):
    db_path = get_persistent_data_path(db_filename)
    driver_was_loaded_here = False

    if driver is None:
        if load_driver_func is None:
            raise ValueError("Must provide a driver or load_driver_func")
        driver = load_driver_func()
        driver_was_loaded_here = True

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(f"""
                SELECT * FROM processed_data
                WHERE connection_sent = 0
                  AND predicted_acceptance >= {min_acceptance_threshold}
                ORDER BY predicted_acceptance DESC
                LIMIT {max_invites}
            """, conn)
    except Exception as e:
        logging.error(f"[DB] Could not load processed_data: {e}")
        return

    if df.empty:
        logging.info("No profiles ready for outreach.")
        return

    logging.info(f"[OUTREACH] Attempting up to {len(df)} invites...")

    pause_after_n = random.randint(*batch_size_range)
    processed_count = 0
    total_sent = 0
    first_visit = True

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(processed_data);")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "connection_sent_time" not in existing_columns:
                cursor.execute("ALTER TABLE processed_data ADD COLUMN connection_sent_time TEXT;")
                logging.info("[DB] Added missing column 'connection_sent_time' to processed_data.")
        conn.commit()


    for _, row in df.iterrows():
        if total_sent >= max_invites:
            break

        url = row.get("profile_url")
        if not url:
            continue

        logging.info(f"[VISIT] {url}")
        try:
            driver.get(url)
            human_sleep(10 if first_visit else 8, 2)
            first_visit = False

            # Scroll to bottom of the page to trigger full content and lazy loading
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            for y in range(0, scroll_height, 80):
                driver.execute_script(f"window.scrollTo(0, {y});")
                time.sleep(0.02)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # stay at bottom
            human_sleep(2.5, 1)

            # force_stabilize_view(driver)  # disabled to avoid automatic upward scroll
            random_hover(driver, "section")
            human_sleep(1.5, 0.5)

            try:
                wait = WebDriverWait(driver, 10)
                debug_buttons = driver.find_elements(By.XPATH, "//main//section[contains(@class, 'pv-top-card')]//button")
                for b in debug_buttons:
                    label = b.text.strip()
                    logging.debug(f"[DEBUG] Top card button found: '{label}'")

                connect_button = wait.until(EC.element_to_be_clickable((By.XPATH, CONNECT_BUTTON_XPATH)))
            except TimeoutException:
                logging.info(f"[SKIP] Skipping profile pretending to be a choosy human, ~1/5 random fail rate to simulate pickyness: {url}")
                continue

            btn_text = connect_button.text.strip().lower()
            if "pending" in btn_text or "withdraw" in btn_text:
                logging.info(f"[SKIP] Already connected or pending: {url}")
                continue

            safe_click(driver, connect_button, url, "Connect")
            logging.info("Clicked 'Connect'")

            try:
                send_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEND_WITHOUT_MESSAGE_SELECTOR)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
                time.sleep(0.3)
                safe_click(driver, send_button, url, "Send without note")
                logging.info("Sent without a note.")
            except TimeoutException:
                logging.info("Connection sent directly or modal skipped.")

            timestamp = datetime.now(timezone.utc).date().isoformat()
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                UPDATE processed_data
                SET connection_sent = 1,
                connection_sent_time = ?
                WHERE profile_url = ?
                """, (timestamp, url))
                logging.info(f"[DB] Marked as sent: {url} at {timestamp}")


            total_sent += 1

        except Exception as e:
            error_msg = ''.join(traceback.format_exception_only(type(e), e)).strip()
            logging.error(f"[ERROR] Failed to connect with {url}: {error_msg}")

        processed_count += 1

        if random.random() < 0.2:
            take_linkedin_detour(driver)
            human_sleep(5, 2)
            random_hover(driver, "a")

        if processed_count >= pause_after_n:
            sleep_time = random.uniform(*break_duration_range)
            logging.info(f"[PAUSE] Sleeping for {sleep_time:.1f}s")
            time.sleep(sleep_time)
            processed_count = 0
            pause_after_n = random.randint(*batch_size_range)

    logging.info(f"[DONE] Invites sent: {total_sent}")

    if not keep_driver_open and driver_was_loaded_here:
        driver.quit()
        logging.info("Driver closed.")

def get_all_connections(driver):
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    driver.set_window_size(1920, 1080)
    time.sleep(3)

    stagnant_scrolls = 0
    last_count = 0

    while True:
        human_scroll(driver, total_scrolls=3)
        time.sleep(2)

        try:
            load_more_btn = driver.find_element(By.XPATH, "//button//span[contains(text(), 'Load more')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
            load_more_btn.click()
            time.sleep(2)
        except Exception:
            pass

        # MUCH BETTER SELECTOR, previously i used one that was very brittle and subject to linkedins random changes
        name_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/') and string-length(text()) > 0]")
        current_count = len(name_elements)

        if current_count == last_count:
            stagnant_scrolls += 1
            logging.info(f"No new names loaded. Streak: {stagnant_scrolls}")
        else:
            stagnant_scrolls = 0
            last_count = current_count

        if stagnant_scrolls >= 3:
            logging.info("Ending scroll: reached stagnant scroll limit.")
            break

    # Extract just names (strip avoids any weird whitespace)
    names = [el.text.strip() for el in name_elements if el.text.strip()]
    logging.info(f"Total connections found: {len(names)}")
    driver.quit()
    return names


def update_connection_accepted(accepted_names, db_filename="linkedin_profiles.db"):
    db_path = get_persistent_data_path(db_filename)

    with sqlite3.connect(db_path) as conn:
        df_sent = pd.read_sql_query(
            "SELECT profile_id, profile_name FROM processed_data WHERE connection_sent = 1",
            conn
        )

        df_sent["name_clean"] = df_sent["profile_name"].str.strip().str.lower()
        accepted_clean = set(name.strip().lower() for name in accepted_names)
        unmatched = accepted_clean - set(df_sent["name_clean"])
        logging.info(f"Unmatched accepted names: {unmatched}")

        matched_ids = df_sent[df_sent["name_clean"].isin(accepted_clean)]["profile_id"].tolist()
        logging.info(f"Matched {len(matched_ids)} accepted connections.")

        for pid in matched_ids:
            conn.execute(
                "UPDATE processed_data SET connection_accepted = 1 WHERE profile_id = ?",
                (pid,)
            )
        conn.commit()

        df_updated = pd.read_sql_query(
            "SELECT * FROM processed_data WHERE connection_sent = 1",
            conn
        )

    logging.info("Connection acceptance update complete.")
    return df_updated

def load_acceptance_metrics(db_filename="linkedin_profiles.db"):
    db_path = get_persistent_data_path(db_filename)
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT connection_sent, connection_accepted FROM processed_data", conn)

    sent = df["connection_sent"].sum()
    accepted = df["connection_accepted"].sum()
    rate = (accepted / sent) * 100 if sent > 0 else 0

    return sent, accepted, round(rate, 2)



#our new feautre that tracks the number of sent connections this week so you dont do what I did on accidentally send 150+ oops

def load_weekly_sent_count(db_filename="linkedin_profiles.db"):
    db_path = get_persistent_data_path(db_filename)
    today = datetime.now(timezone.utc).date()
    last_monday = today - timedelta(days=today.weekday())

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data
            WHERE connection_sent = 1 AND connection_sent_time >= ?
        """, (last_monday.isoformat(),))
        result = cursor.fetchone()[0]
    
    return result
