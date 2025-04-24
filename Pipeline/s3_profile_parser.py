import os
import sys
import re
import sqlite3
import logging
from bs4 import BeautifulSoup
from Pipeline.util_human_mimic import human_sleep, human_scroll, random_hover, take_linkedin_detour
from Pipeline.util_paths import get_persistent_data_path, load_config, ensure_dir

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

#The previous step in our pipeline was html_extraction.py
#we raw html and dumped into a cache folder
#we now want to parse this html and extract the relevant data
#This is the class we use to parse the extracted HTML locally

class ProfileParser:

    def __init__(self, cache_subdir="html_cache", db_filename="linkedin_profiles.db"):
        self.db_path = get_persistent_data_path(db_filename)
        self.cache_dir = os.path.join(os.path.dirname(self.db_path), cache_subdir)


    #loads html for a given id
    def load_html(self, profile_id):
        path = os.path.join(self.cache_dir, f"profile_{profile_id}.html")
        if not os.path.exists(path):
            logging.warning(f"File not found: {path}")
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def is_already_processed(self, profile_id):
        if not os.path.exists(self.db_path):
            return False  # No DB at all, so definitely not processed

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

            # Check if the table exists FIRST
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='processed_data'
                """)
                if cursor.fetchone() is None:
                    # Table doesn't exist yet → so nothing can be processed yet
                    return False

                # Only run this if table exists:
                cursor.execute("SELECT 1 FROM processed_data WHERE profile_id = ?", (profile_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logging.warning(f"Error checking if profile is already processed: {e}")
            return False

    
    def get_unprocessed_profile_ids(self, limit=100):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Select IDs from profiles table that are not yet in processed_data
                cursor.execute("""
                    SELECT profile_id FROM profiles
                    WHERE profile_id NOT IN (SELECT profile_id FROM processed_data)
                    ORDER BY profile_id ASC
                    LIMIT ?
                """, (limit,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.warning(f"Error loading unprocessed profiles: {e}")
            return []

    #this is a simple function to get the connection count from the html
    def get_connection_count(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        for span in soup.find_all('span', class_='t-bold'):
            parent = span.find_parent('span')
            if parent and 'connection' in parent.get_text(strip=True).lower():
                return span.get_text(strip=True)
        return None
    
    #this is the main function to extract the experience entries from the html
    #we use BeautifulSoup to parse the html and extract the relevant data
    def extract_experience_entries(self, html):
        soup = BeautifulSoup(html, "html.parser")
        experience_entries = []
        for section in soup.find_all("li", class_="artdeco-list__item"):
            title_tag = section.find("div", class_="t-bold")
            company_tag = section.find("span", class_="t-14 t-normal")
            date_tag = section.find("span", class_="pvs-entity__caption-wrapper")
            location_tag = section.find_all("span", class_="t-14 t-normal t-black--light")

            title = title_tag.get_text(strip=True) if title_tag else None
            company = company_tag.get_text(strip=True) if company_tag else None
            date = date_tag.get_text(strip=True) if date_tag else None
            location = location_tag[1].get_text(strip=True) if len(location_tag) > 1 else None

            if title and company:
                experience_entries.append({
                    "title": title,
                    "company": company,
                    "date_range": date,
                    "location": location
                })
        return experience_entries
    
    #this function cleans the experience entries by removing duplicates and invalid date ranges
    def clean_experience_entries(self, experiences):
        def dedupe_string(s):
            if not s: return s
            s = s.strip()
            mid = len(s) // 2
            return s[:mid] if s[:mid] == s[mid:] else s
  
        def is_valid_date_range(date_str):
            if not date_str:
                return False
            date_str = date_str.strip()
            patterns = [
                r'^[A-Za-z]{3} \d{4} - [A-Za-z]{3,7} \d{4}',
                r'^[A-Za-z]{3} \d{4} - Present',
                r'^Issued [A-Za-z]{3,9} \d{4}',
                r'^\d{4} - \d{4}',
                r'^\d{4} - Present'
            ]
            return any(re.search(p, date_str) for p in patterns)

        cleaned = []
        for entry in experiences:
            title = dedupe_string(entry.get('title', '')).strip()
            company = dedupe_string(entry.get('company', '')).strip()
            date_range = entry.get('date_range', '').strip() if entry.get('date_range') else None
            location = dedupe_string(entry.get('location', '')).strip() if entry.get('location') else None

            if not title or "You both studied" in title or "profile" in title.lower():
                continue
            if date_range and not is_valid_date_range(date_range):
                continue

            cleaned.append({
                'title': title,
                'company': company,
                'date_range': date_range,
                'location': location,
            })
        return cleaned
    
    #this function extracts the descriptive spans from the html, basically the core text blocks with each experience added
    def extract_descriptive_spans(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        raw_blocks = []

        for span in soup.find_all('span', attrs={"aria-hidden": "true"}):
            txt = span.get_text(strip=True)
            if txt:
                raw_blocks.append(txt)

        for span in soup.find_all('span', class_="visually-hidden"):
            txt = span.get_text(strip=True)
            if txt and txt not in raw_blocks:
                raw_blocks.append(txt)

        return raw_blocks
    
    #used to parse out random junk html we accidentally pulled
    def filter_long_text_blocks(self, text_blocks, min_length=100):
        return [t.strip() for t in text_blocks if len(t.strip()) >= min_length]
    

    #this function is the main entry point for parsing a profile
    def parse_profile(self, profile_id):
        if self.is_already_processed(profile_id):
            return None

        html = self.load_html(profile_id)
        if html is None:
            return None

        conn_count = self.get_connection_count(html)
        raw_experiences = self.extract_experience_entries(html)
        clean_experiences = self.clean_experience_entries(raw_experiences)
        text_blocks = self.extract_descriptive_spans(html)
        long_texts = self.filter_long_text_blocks(text_blocks)

        return {
            "profile_id": profile_id,
            "connection_count": conn_count,
            "experiences": clean_experiences,
            "raw_text": " ".join(long_texts)
        }
