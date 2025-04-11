import os
import sys
import sqlite3
import pandas as pd
import joblib
import logging
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from Pipeline.util_paths import get_persistent_data_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class ModelTrainer:
    def __init__(self, db_path="linkedin_profiles.db", model_subdir="models", model_type="logistic"):
    
        self.db_path = get_persistent_data_path(db_path)

        self.model_dir = os.path.dirname(get_persistent_data_path(os.path.join(model_subdir, "dummy")))

        ensure_dir(self.model_dir)

        self.model_type = model_type

    def load_training_data(self):
        """Load processed outreach data where connection_sent = 1 and accepted is known (0 or 1)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT * FROM processed_data
                    WHERE connection_sent = 1
                """, conn)
            df = df[df["connection_accepted"].isin([0, 1])]
            return df
        except Exception as e:
            logging.error(f"Failed to load training data: {e}")
            return pd.DataFrame()

    def train_model(self, df):
        """Train a model using selected features and return the trained model."""
        features = [
            "tag_h1_coordination_game", "tag_h2_status_seekers",
            "tag_h3_shared_interests", "tag_h4_profile_effort",
            "tag_h5_likely_female"
        ]
        X = df[features]
        y = df["connection_accepted"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        if self.model_type == "logistic":
            model = LogisticRegression(max_iter=1000)
        elif self.model_type == "random_forest":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError("Unsupported model type. Use 'logistic' or 'random_forest'.")

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        logging.info("\n[REPORT] Classification Report:\n")
        logging.info("\n" + classification_report(y_test, y_pred))

        return model

    def save_model(self, model, filename=None):
        """Save trained model to the model directory with timestamped filename."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{self.model_type}_model_{timestamp}.joblib"

        model_path = os.path.join(self.model_dir, filename)
        try:
            joblib.dump(model, model_path)
            logging.info(f"\n[SUCCESS] Model saved to {model_path}")
        except Exception as e:
            logging.error(f"Failed to save model: {e}")

    def run(self):
        """Main method to train and save a model if sufficient data is available."""
        logging.info(f"Attempting to open DB at: {self.db_path}")
        df = self.load_training_data()
        if df.empty:
            logging.info("Not enough labeled data to train a model.")
            return

        model = self.train_model(df)
        self.save_model(model)
