import os
import sys
import sqlite3
import pandas as pd
import joblib
import logging

from Pipeline.util_paths import load_config, resource_path, get_persistent_data_path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

#the previous step in our pipeline was preprocessing.py
#we have a db of model ready data, now just have to load and use a model
#this class handles all that

class ModelPredictor:
   

    def __init__(self):
        config = load_config()

        model_rel_path = config.get("model_path", "models/default_model.joblib")
        self.model_path = resource_path(model_rel_path)

        db_filename = os.path.basename(config.get("db_path", "linkedin_profiles.db"))
        self.db_path = get_persistent_data_path(db_filename)

        self.model = self.load_model()
    
    #loads whatever model path you give it
    def load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

        logging.info(f"[LOAD MODEL] Loading model from: {self.model_path}")
        return joblib.load(self.model_path)


    def fetch_unsent_profiles(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT profile_id, profile_url, profile_name, connection_sent,
                           tag_h1_coordination_game, tag_h2_status_seekers,
                           tag_h3_shared_interests, tag_h4_profile_effort,
                           tag_h5_likely_female
                    FROM processed_data
                    WHERE connection_sent = 0
                """
                return pd.read_sql_query(query, conn)
        except Exception as e:
            logging.error(f"Error fetching unsent profiles: {e}")
            return pd.DataFrame()

    def predict(self, df):
        features = [
            "tag_h1_coordination_game", "tag_h2_status_seekers",
            "tag_h3_shared_interests", "tag_h4_profile_effort",
            "tag_h5_likely_female"
        ]
        try:
            X = df[features]
            predictions = self.model.predict_proba(X)[:, 1]
            df["predicted_acceptance"] = predictions
            return df
        except Exception as e:
            logging.error(f"Prediction failed: {e}")
            return df

    def update_predictions_in_db(self, df):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    cursor.execute("""
                        UPDATE processed_data
                        SET predicted_acceptance = ?
                        WHERE profile_id = ?
                    """, (row["predicted_acceptance"], row["profile_id"]))
                conn.commit()
            logging.info(f"[DB] Updated predictions for {len(df)} profiles.")
        except Exception as e:
            logging.error(f"Failed to update predictions in DB: {e}")

    def run(self):
        df = self.fetch_unsent_profiles()
        if df.empty:
            logging.info("No profiles available for prediction.")
            return pd.DataFrame()

        df = self.predict(df)
        if "predicted_acceptance" in df.columns:
            self.update_predictions_in_db(df)

        ready_df = df[df["predicted_acceptance"] >= 0.01].copy()
        ready_df = ready_df.sort_values(by="predicted_acceptance", ascending=False).reset_index(drop=True)

        logging.info(f"[READY] {len(ready_df)} profiles ready for outreach.")
        return ready_df

