# Auto_Connect
AutoConnect is a Python-based desktop automation tool that streamlines cold LinkedIn outreach by scraping profiles, predicting acceptance likelihood using machine learning, and sending smart, human-like connection requests — all through a simple GUI.

Built for Linux development, with bundling support for Windows distribution.

### Features
🧩 Modular pipeline: scrape → parse → tag → predict → connect

🔍 Selenium-based scraping that mimics real user behavior

📊 ML model (scikit-learn) predicts which profiles are most likely to accept

📊 Training New Models (scikit-learn) allows for retraining with more data 

📈 tracker of invites and accepted connections

⚙️ Configurable config.json (interests, thresholds, model paths)


### 🐧 Designed for Linux — Deployable to Windows
Developed and tested on Debian Linux

Uses PyInstaller for cross-compiling to .exe

Fully standalone .exe can run on Windows machines without Python (hopefully whenever I can borrow my housemates laptop we'll find out)


### 📚 How to Use
Set up your LinkedIn targeting config

Run the GUI and start scraping

Let the model score and rank connection likelihood

Review results or let the bot send smart invites

Track which ones get accepted
