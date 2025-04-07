import os
import re
import ast
import json
import sqlite3
import pandas as pd
import numpy as np
import gender_guesser.detector as gender
import sys
import logging
from functions.utils import get_persistent_data_path, load_config

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class DataPreprocessing:
    def __init__(self, df_raw):
        self.df_raw = df_raw.copy()
        self.df_clean = None
        self.df_tagged = None

        config = load_config()
        self.interest_keywords = config.get("interest_keywords", [])

    def clean_connection_count(self, val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().lower().replace(",", "")
        if "500+" in val:
            return 500.0
        match = re.search(r"(\d+)", val)
        return float(match.group(1)) if match else np.nan

    def safely_parse_list(self, val):
        if isinstance(val, str):
            try:
                parsed = ast.literal_eval(val)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return []

    def count_experience_items(self, val):
        return len(val) if isinstance(val, list) else 0

    def count_interest_keywords(self, text):
        if isinstance(text, str):
            text_lower = text.lower()
            return sum(kw in text_lower for kw in self.interest_keywords)
        return 0

    def is_likely_female(self, name):
        gd = gender.Detector(case_sensitive=False)
        prediction = gd.get_gender(name)
        return 1 if prediction in ['female', 'mostly_female'] else 0

    def merge_name_and_url_from_db(self, df):
        db_path = get_persistent_data_path("linkedin_profiles.db")
        try:
            with sqlite3.connect(db_path) as conn:
                mapping_df = pd.read_sql_query(
                    "SELECT profile_id, name AS profile_name, profile_url FROM profiles",
                    conn
                )
            return df.merge(mapping_df, on="profile_id", how="left")
        except Exception as e:
            logging.error(f"Failed to merge name/url from DB: {e}")
            return df

    def run_cleaning(self):
        df = self.df_raw.dropna(subset=["connection_count", "experiences"]).copy()

        df["connection_count"] = df["connection_count"].apply(self.clean_connection_count)
        df["experiences"] = df["experiences"].apply(self.safely_parse_list)
        df["n_experiences"] = df["experiences"].apply(self.count_experience_items)
        df["len_raw_text"] = df["raw_text"].apply(lambda x: len(x.split()) if isinstance(x, str) else 0)
        df["same_interest_score"] = df["raw_text"].apply(self.count_interest_keywords)

        df = self.merge_name_and_url_from_db(df)
        self.df_clean = df
        return self.df_clean

    def run_tagging(self):
        if self.df_clean is None:
            raise ValueError("Must run run_cleaning() before tagging.")

        df = self.df_clean.copy()

        df["tag_h1_coordination_game"] = df["connection_count"].apply(lambda x: 1 if 20 < x <= 100 else 0)
        df["tag_h2_status_seekers"] = df["connection_count"].apply(lambda x: 1 if 400 <= x < 500 else 0)
        df["tag_h3_shared_interests"] = df["same_interest_score"].apply(lambda x: 1 if x >= 4 else 0)
        df["tag_h4_profile_effort"] = df["len_raw_text"].apply(lambda x: 1 if x > 600 else 0)
        df["first_name"] = df["profile_name"].str.split().str[0]
        df["tag_h5_likely_female"] = df["first_name"].apply(self.is_likely_female)

        df["connection_sent"] = 0
        df["connection_accepted"] = 0
        df["predicted_acceptance"] = np.nan

        cols = [
            "profile_id", "profile_name", "profile_url",
            "tag_h1_coordination_game", "tag_h2_status_seekers",
            "tag_h3_shared_interests", "tag_h4_profile_effort",
            "tag_h5_likely_female", "connection_sent", "connection_accepted",
            "predicted_acceptance"
        ]

        self.df_tagged = df[cols].copy()
        return self.df_tagged

    def save_to_database(self, table_name="processed_data"):
        if self.df_tagged is None:
            raise ValueError("No tagged data to save. Run run_tagging() first.")

        db_path = get_persistent_data_path("linkedin_profiles.db")
        try:
            with sqlite3.connect(db_path) as conn:
                self.df_tagged.to_sql(table_name, conn, if_exists="append", index=False)
                logging.info(f"[SUCCESS] Appended {len(self.df_tagged)} rows to '{table_name}' in {db_path}")
        except Exception as e:
            logging.error(f"[ERROR] Failed to write to database: {e}")
